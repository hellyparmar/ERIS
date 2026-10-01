from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Category, InventoryItem, Outlet, Product, Sale, SaleItem, Supplier, User
from app.routers.common import csv_response, get_or_404, page_response, paginate
from app.schemas import CategoryIn, ProductIn
from app.security import get_current_user, require_manager, scoped_outlet_ids
from app.services import analytics as A
from app.services.inventory import stock_status

router = APIRouter(prefix="/api", tags=["products"])


# ------------------------------------------------------------------------------------------ categories
@router.get("/categories")
def list_categories(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    counts = dict(db.execute(select(Product.category_id, func.count(Product.id)).group_by(Product.category_id)).all())
    return [{"id": c.id, "name": c.name, "products": counts.get(c.id, 0)}
            for c in db.scalars(select(Category).order_by(Category.name)).all()]


@router.post("/categories", status_code=201)
def create_category(body: CategoryIn, _: User = Depends(require_manager), db: Session = Depends(get_db)):
    if db.scalar(select(Category.id).where(func.lower(Category.name) == body.name.strip().lower())):
        raise HTTPException(409, "Category already exists")
    c = Category(name=body.name.strip())
    db.add(c)
    db.commit()
    return {"id": c.id, "name": c.name, "products": 0}


@router.put("/categories/{cat_id}")
def rename_category(cat_id: int, body: CategoryIn, _: User = Depends(require_manager), db: Session = Depends(get_db)):
    c = get_or_404(db, Category, cat_id, "Category")
    clash = db.scalar(select(Category.id).where(func.lower(Category.name) == body.name.strip().lower(), Category.id != cat_id))
    if clash:
        raise HTTPException(409, "Category already exists")
    c.name = body.name.strip()
    db.commit()
    return {"id": c.id, "name": c.name}


@router.delete("/categories/{cat_id}")
def delete_category(cat_id: int, _: User = Depends(require_manager), db: Session = Depends(get_db)):
    c = get_or_404(db, Category, cat_id, "Category")
    if db.scalar(select(func.count(Product.id)).where(Product.category_id == cat_id)):
        raise HTTPException(400, "Move or delete the products in this category first")
    db.delete(c)
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------------------------------ products
def product_dict(p: Product) -> dict:
    margin = p.selling_price - p.selling_price * p.tax_rate / (100 + p.tax_rate) - p.cost_price
    net = p.selling_price - p.selling_price * p.tax_rate / (100 + p.tax_rate)
    return {"id": p.id, "sku": p.sku, "name": p.name, "category_id": p.category_id,
            "category": p.category.name if p.category else None, "supplier_id": p.supplier_id,
            "supplier": p.supplier.name if p.supplier else None, "unit": p.unit, "cost_price": p.cost_price,
            "selling_price": p.selling_price, "tax_rate": p.tax_rate, "reorder_level": p.reorder_level,
            "is_active": p.is_active, "margin_pct": round(margin / net * 100, 1) if net else 0}


@router.get("/products")
def list_products(search: str | None = None, category_id: int | None = None, supplier_id: int | None = None,
                  active: bool | None = True, page: int = 1, page_size: int = Query(50, le=500),
                  sort: str = "name", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    outlet_ids = scoped_outlet_ids(user)
    anchor = A.anchor_date(db)
    stock_sq = select(InventoryItem.product_id, func.sum(InventoryItem.quantity).label("stock"))
    if outlet_ids:
        stock_sq = stock_sq.where(InventoryItem.outlet_id.in_(outlet_ids))
    stock_sq = stock_sq.group_by(InventoryItem.product_id).subquery()
    sold_sq = select(SaleItem.product_id, func.sum(SaleItem.quantity).label("units"),
                     func.sum(SaleItem.line_total).label("revenue")).join(Sale, Sale.id == SaleItem.sale_id).where(
        A.COMPLETED, SaleItem.sale_date > anchor - timedelta(days=30))
    if outlet_ids:
        sold_sq = sold_sq.where(SaleItem.outlet_id.in_(outlet_ids))
    sold_sq = sold_sq.group_by(SaleItem.product_id).subquery()

    q = select(Product, stock_sq.c.stock, sold_sq.c.units, sold_sq.c.revenue).outerjoin(
        stock_sq, stock_sq.c.product_id == Product.id).outerjoin(sold_sq, sold_sq.c.product_id == Product.id)
    if search:
        like = f"%{search.strip()}%"
        q = q.where(or_(Product.name.ilike(like), Product.sku.ilike(like)))
    if category_id:
        q = q.where(Product.category_id == category_id)
    if supplier_id:
        q = q.where(Product.supplier_id == supplier_id)
    if active is not None:
        q = q.where(Product.is_active.is_(active))
    order = {"name": Product.name.asc(), "sku": Product.sku.asc(), "price": Product.selling_price.desc(),
             "revenue": func.coalesce(sold_sq.c.revenue, 0).desc(), "units": func.coalesce(sold_sq.c.units, 0).desc(),
             "stock": func.coalesce(stock_sq.c.stock, 0).asc()}.get(sort, Product.name.asc())
    rows, total = paginate(db, q.order_by(order), page, page_size)
    items = [{**product_dict(p), "stock": round(stock or 0, 1), "units_30d": round(units or 0, 1),
              "revenue_30d": round(rev or 0, 2)} for p, stock, units, rev in rows]
    return page_response(items, total, page, page_size)


@router.get("/products/export")
def export_products(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = [[p.sku, p.name, p.category.name, p.unit, p.cost_price, p.selling_price, p.tax_rate, p.reorder_level,
             p.supplier.name if p.supplier else ""] for p in db.scalars(select(Product).order_by(Product.sku)).all()]
    return csv_response("products.csv", ["sku", "name", "category", "unit", "cost_price", "selling_price", "tax_rate",
                                         "reorder_level", "supplier"], rows)


@router.get("/products/{product_id}")
def get_product(product_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = get_or_404(db, Product, product_id, "Product")
    outlet_ids = scoped_outlet_ids(user)
    anchor = A.anchor_date(db)
    demand = A.avg_daily_units_by_outlet_product(db, 28, anchor)
    q = select(InventoryItem, Outlet).join(Outlet, Outlet.id == InventoryItem.outlet_id).where(
        InventoryItem.product_id == p.id).order_by(Outlet.id)
    if outlet_ids:
        q = q.where(InventoryItem.outlet_id.in_(outlet_ids))
    stock = []
    for inv, o in db.execute(q).all():
        rate = demand.get((o.id, p.id), 0)
        stock.append({"outlet_id": o.id, "outlet": o.name, "quantity": inv.quantity, "reorder_level": inv.reorder_level,
                      "avg_daily_demand": round(rate, 2), "days_of_cover": round(inv.quantity / rate, 1) if rate else None,
                      "status": stock_status(inv.quantity, inv.reorder_level)})
    rng90 = A.DateRange(anchor - timedelta(days=89), anchor)
    rng30 = A.DateRange(anchor - timedelta(days=29), anchor)
    stats = A.top_products(db, rng30, outlet_ids, 1, product_ids=[p.id])
    prev = A.top_products(db, rng30.previous(), outlet_ids, 1, product_ids=[p.id])
    return {
        **product_dict(p),
        "stock_by_outlet": stock,
        "total_stock": round(sum(s["quantity"] for s in stock), 1),
        "last_30_days": stats[0] if stats else {"units": 0, "revenue": 0, "profit": 0},
        "previous_30_days": prev[0] if prev else {"units": 0, "revenue": 0, "profit": 0},
        "trend": A.revenue_series(db, rng90, outlet_ids, "week", product_id=p.id),
        "bought_with": [x for x in A.product_affinity(db, rng90, outlet_ids, limit=300, min_pair_count=10)
                        if p.id in (x["product_a_id"], x["product_b_id"])][:5],
    }


def _check_refs(db: Session, body: ProductIn) -> None:
    get_or_404(db, Category, body.category_id, "Category")
    if body.supplier_id:
        get_or_404(db, Supplier, body.supplier_id, "Supplier")


@router.post("/products", status_code=201)
def create_product(body: ProductIn, _: User = Depends(require_manager), db: Session = Depends(get_db)):
    if db.scalar(select(Product.id).where(Product.sku == body.sku)):
        raise HTTPException(409, f"SKU {body.sku} already exists")
    _check_refs(db, body)
    p = Product(**body.model_dump())
    db.add(p)
    db.flush()
    for o in db.scalars(select(Outlet)).all():
        db.add(InventoryItem(outlet_id=o.id, product_id=p.id, quantity=0, reorder_level=p.reorder_level))
    db.commit()
    db.refresh(p)
    return product_dict(p)


@router.put("/products/{product_id}")
def update_product(product_id: int, body: ProductIn, _: User = Depends(require_manager), db: Session = Depends(get_db)):
    p = get_or_404(db, Product, product_id, "Product")
    if body.sku != p.sku and db.scalar(select(Product.id).where(Product.sku == body.sku)):
        raise HTTPException(409, f"SKU {body.sku} already exists")
    _check_refs(db, body)
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return product_dict(p)


@router.delete("/products/{product_id}")
def delete_product(product_id: int, _: User = Depends(require_manager), db: Session = Depends(get_db)):
    p = get_or_404(db, Product, product_id, "Product")
    from app.models import PurchaseOrderItem

    used = db.scalar(select(func.count(SaleItem.id)).where(SaleItem.product_id == p.id)) or db.scalar(
        select(func.count(PurchaseOrderItem.id)).where(PurchaseOrderItem.product_id == p.id))
    if used:
        p.is_active = False
        db.commit()
        return {"ok": True, "deactivated": True,
                "message": "Product has sales or purchase history, so it was deactivated instead of deleted."}
    db.delete(p)
    db.commit()
    return {"ok": True, "deleted": True}
