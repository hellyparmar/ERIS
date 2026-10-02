"""Suppliers and customers (the 'contacts' of the business)."""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Customer, Product, PurchaseOrder, Sale, SaleItem, Supplier, User
from app.routers.common import csv_response, get_or_404, page_response, paginate
from app.schemas import CustomerIn, SupplierIn
from app.security import get_current_user, require_manager, require_writer, scoped_outlet_ids
from app.services import analytics as A
from app.services.sales import normalize_phone

router = APIRouter(prefix="/api", tags=["suppliers & customers"])


# ------------------------------------------------------------------------------------------ suppliers
def supplier_dict(s: Supplier) -> dict:
    return {k: getattr(s, k) for k in ("id", "name", "contact_person", "phone", "email", "city", "lead_time_days",
                                       "payment_terms", "notes", "is_active")}


@router.get("/suppliers")
def list_suppliers(search: str | None = None, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(Supplier).order_by(Supplier.name)
    if search:
        q = q.where(or_(Supplier.name.ilike(f"%{search}%"), Supplier.city.ilike(f"%{search}%")))
    products = dict(db.execute(select(Product.supplier_id, func.count(Product.id)).where(
        Product.is_active.is_(True)).group_by(Product.supplier_id)).all())
    open_po = {sid: (n, v) for sid, n, v in db.execute(select(
        PurchaseOrder.supplier_id, func.count(PurchaseOrder.id), func.sum(PurchaseOrder.total_cost)).where(
        PurchaseOrder.status == "ordered").group_by(PurchaseOrder.supplier_id)).all()}
    anchor = A.anchor_date(db)
    spend = dict(db.execute(select(PurchaseOrder.supplier_id, func.sum(PurchaseOrder.total_cost)).where(
        PurchaseOrder.status == "received", PurchaseOrder.received_date > anchor - timedelta(days=90)).group_by(
        PurchaseOrder.supplier_id)).all())
    out = []
    for s in db.scalars(q).all():
        n, v = open_po.get(s.id, (0, 0))
        out.append({**supplier_dict(s), "products": products.get(s.id, 0), "open_orders": n,
                    "open_order_value": round(v or 0, 2), "purchases_90d": round(spend.get(s.id, 0) or 0, 2)})
    return out


@router.get("/suppliers/{supplier_id}")
def get_supplier(supplier_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = get_or_404(db, Supplier, supplier_id, "Supplier")
    products = db.scalars(select(Product).where(Product.supplier_id == s.id).order_by(Product.name)).all()
    orders = db.scalars(select(PurchaseOrder).where(PurchaseOrder.supplier_id == s.id).order_by(
        PurchaseOrder.order_date.desc()).limit(20)).all()
    received = [o for o in orders if o.status == "received" and o.received_date and o.expected_date]
    on_time = sum(1 for o in received if o.received_date <= o.expected_date)
    return {
        **supplier_dict(s),
        "products": [{"id": p.id, "sku": p.sku, "name": p.name, "cost_price": p.cost_price, "unit": p.unit,
                      "is_active": p.is_active} for p in products],
        "recent_orders": [{"id": o.id, "po_number": o.po_number, "outlet": o.outlet.name, "status": o.status,
                           "order_date": o.order_date.isoformat(), "total_cost": o.total_cost} for o in orders],
        "on_time_rate_pct": round(on_time / len(received) * 100, 1) if received else None,
    }


@router.post("/suppliers", status_code=201)
def create_supplier(body: SupplierIn, _: User = Depends(require_manager), db: Session = Depends(get_db)):
    if db.scalar(select(Supplier.id).where(func.lower(Supplier.name) == body.name.strip().lower())):
        raise HTTPException(409, "A supplier with this name already exists")
    s = Supplier(**body.model_dump())
    db.add(s)
    db.commit()
    return supplier_dict(s)


@router.put("/suppliers/{supplier_id}")
def update_supplier(supplier_id: int, body: SupplierIn, _: User = Depends(require_manager), db: Session = Depends(get_db)):
    s = get_or_404(db, Supplier, supplier_id, "Supplier")
    clash = db.scalar(select(Supplier.id).where(func.lower(Supplier.name) == body.name.strip().lower(),
                                                Supplier.id != supplier_id))
    if clash:
        raise HTTPException(409, "A supplier with this name already exists")
    for k, v in body.model_dump().items():
        setattr(s, k, v)
    db.commit()
    return supplier_dict(s)


@router.delete("/suppliers/{supplier_id}")
def delete_supplier(supplier_id: int, _: User = Depends(require_manager), db: Session = Depends(get_db)):
    s = get_or_404(db, Supplier, supplier_id, "Supplier")
    if db.scalar(select(func.count(PurchaseOrder.id)).where(PurchaseOrder.supplier_id == s.id)):
        s.is_active = False
        db.commit()
        return {"ok": True, "deactivated": True,
                "message": "Supplier has purchase orders, so it was marked inactive instead of deleted."}
    db.delete(s)
    db.commit()
    return {"ok": True, "deleted": True}


# ------------------------------------------------------------------------------------------ customers
def customer_dict(c: Customer) -> dict:
    return {"id": c.id, "name": c.name, "phone": c.phone, "email": c.email, "city": c.city,
            "customer_type": c.customer_type, "notes": c.notes,
            "created_at": c.created_at.isoformat() if c.created_at else None}


@router.get("/customers")
def list_customers(search: str | None = None, customer_type: str | None = None, sort: str = "spend",
                   page: int = 1, page_size: int = Query(50, le=500), user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    outlet_ids = scoped_outlet_ids(user)
    stats = select(Sale.customer_id, func.count(Sale.id).label("orders"), func.sum(Sale.total).label("spend"),
                   func.max(Sale.sale_date).label("last")).where(A.COMPLETED, Sale.customer_id.is_not(None))
    if outlet_ids:
        stats = stats.where(Sale.outlet_id.in_(outlet_ids))
    stats = stats.group_by(Sale.customer_id).subquery()
    q = select(Customer, stats.c.orders, stats.c.spend, stats.c.last).outerjoin(stats, stats.c.customer_id == Customer.id)
    if outlet_ids:
        q = q.where(stats.c.orders.is_not(None))
    if search:
        like = f"%{search.strip()}%"
        digits = normalize_phone(search) or "~"
        q = q.where(or_(Customer.name.ilike(like), Customer.phone.like(f"%{digits}%"), Customer.email.ilike(like)))
    if customer_type:
        q = q.where(Customer.customer_type == customer_type)
    order = {"spend": func.coalesce(stats.c.spend, 0).desc(), "orders": func.coalesce(stats.c.orders, 0).desc(),
             "recent": stats.c.last.desc(), "name": Customer.name.asc(), "new": Customer.created_at.desc()
             }.get(sort, func.coalesce(stats.c.spend, 0).desc())
    rows, total = paginate(db, q.order_by(order, Customer.id), page, page_size)
    items = [{**customer_dict(c), "orders": orders or 0, "spend": round(spend or 0, 2),
              "last_purchase": last.isoformat() if last else None} for c, orders, spend, last in rows]
    return page_response(items, total, page, page_size)


@router.get("/customers/export")
def export_customers(_: User = Depends(require_manager), db: Session = Depends(get_db)):
    rows = [[c.name, c.phone or "", c.email or "", c.city or "", c.customer_type]
            for c in db.scalars(select(Customer).order_by(Customer.name)).all()]
    return csv_response("customers.csv", ["name", "phone", "email", "city", "customer_type"], rows)


@router.get("/customers/{customer_id}")
def get_customer(customer_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = get_or_404(db, Customer, customer_id, "Customer")
    outlet_ids = scoped_outlet_ids(user)
    q = select(Sale).where(Sale.customer_id == c.id, A.COMPLETED)
    if outlet_ids:
        q = q.where(Sale.outlet_id.in_(outlet_ids))
    sales = db.scalars(q.order_by(Sale.sold_at.desc()).limit(25)).all()
    agg = db.execute(select(func.count(Sale.id), func.sum(Sale.total), func.min(Sale.sale_date), func.max(Sale.sale_date))
                     .where(Sale.customer_id == c.id, A.COMPLETED)).one()
    fav = db.execute(select(Product.name, func.sum(SaleItem.quantity).label("q")).join(Sale, Sale.id == SaleItem.sale_id)
                     .join(Product, Product.id == SaleItem.product_id).where(Sale.customer_id == c.id, A.COMPLETED)
                     .group_by(Product.name).order_by(func.sum(SaleItem.quantity).desc()).limit(5)).all()
    rfm = A.customer_rfm(db)
    seg = rfm.loc[rfm["customer_id"] == c.id, "segment"]
    orders, spend, first, last = agg
    return {
        **customer_dict(c),
        "orders": orders or 0, "spend": round(spend or 0, 2), "avg_bill": round((spend or 0) / orders, 2) if orders else 0,
        "first_purchase": first.isoformat() if first else None, "last_purchase": last.isoformat() if last else None,
        "segment": seg.iloc[0] if len(seg) else None,
        "favourite_products": [{"name": n, "quantity": round(q, 1)} for n, q in fav],
        "recent_sales": [{"id": s.id, "invoice_no": s.invoice_no, "outlet": s.outlet.name,
                          "sold_at": s.sold_at.isoformat(), "total": s.total, "items": s.items_count,
                          "payment_method": s.payment_method} for s in sales],
    }


def _phone_unique(db: Session, phone: str | None, exclude_id: int | None = None) -> str | None:
    phone = normalize_phone(phone)
    if phone:
        if len(phone) < 10:
            raise HTTPException(400, "Phone number must have 10 digits")
        q = select(Customer.id).where(Customer.phone == phone)
        if exclude_id:
            q = q.where(Customer.id != exclude_id)
        if db.scalar(q):
            raise HTTPException(409, "Another customer already uses this phone number")
    return phone


@router.post("/customers", status_code=201)
def create_customer(body: CustomerIn, _: User = Depends(require_writer), db: Session = Depends(get_db)):
    data = body.model_dump()
    data["phone"] = _phone_unique(db, body.phone)
    c = Customer(**data)
    db.add(c)
    db.commit()
    return customer_dict(c)


@router.put("/customers/{customer_id}")
def update_customer(customer_id: int, body: CustomerIn, _: User = Depends(require_writer),
                    db: Session = Depends(get_db)):
    c = get_or_404(db, Customer, customer_id, "Customer")
    data = body.model_dump()
    data["phone"] = _phone_unique(db, body.phone, customer_id)
    for k, v in data.items():
        setattr(c, k, v)
    db.commit()
    return customer_dict(c)


@router.delete("/customers/{customer_id}")
def delete_customer(customer_id: int, _: User = Depends(require_manager), db: Session = Depends(get_db)):
    c = get_or_404(db, Customer, customer_id, "Customer")
    if db.scalar(select(func.count(Sale.id)).where(Sale.customer_id == c.id)):
        raise HTTPException(400, "This customer has purchase history and cannot be deleted")
    db.delete(c)
    db.commit()
    return {"ok": True}
