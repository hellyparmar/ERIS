from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Customer, Outlet, Product, Sale, SaleItem, User
from app.routers.common import csv_response, get_or_404, page_response, paginate
from app.schemas import SaleIn, VoidIn
from app.security import ensure_outlet_access, get_current_user, require_manager, scoped_outlet_ids
from app.services import forecasting as F
from app.services.sales import LineInput, SaleInput, create_sale, void_sale

router = APIRouter(prefix="/api/sales", tags=["sales"])


def sale_dict(s: Sale, detail: bool = False) -> dict:
    d = {"id": s.id, "invoice_no": s.invoice_no, "outlet_id": s.outlet_id, "outlet": s.outlet.name,
         "customer_id": s.customer_id, "customer": s.customer.name if s.customer else None,
         "customer_phone": s.customer.phone if s.customer else None, "sold_at": s.sold_at.isoformat(),
         "channel": s.channel, "payment_method": s.payment_method, "subtotal": s.subtotal, "discount": s.discount,
         "tax_amount": s.tax_amount, "total": s.total, "items_count": s.items_count, "status": s.status,
         "source": s.source, "notes": s.notes}
    if detail:
        d["items"] = [{"product_id": i.product_id, "sku": i.product.sku, "product": i.product.name,
                       "unit": i.product.unit, "quantity": i.quantity, "unit_price": i.unit_price,
                       "discount": i.discount, "tax_amount": i.tax_amount, "line_total": i.line_total,
                       "tax_rate": i.product.tax_rate} for i in s.items]
    return d


def _filtered(user: User, outlet_id, start, end, payment_method, channel, status, search):
    outlet_ids = scoped_outlet_ids(user, outlet_id)
    q = select(Sale).outerjoin(Customer, Customer.id == Sale.customer_id)
    if outlet_ids:
        q = q.where(Sale.outlet_id.in_(outlet_ids))
    if start:
        q = q.where(Sale.sale_date >= start)
    if end:
        q = q.where(Sale.sale_date <= end)
    if payment_method:
        q = q.where(Sale.payment_method == payment_method)
    if channel:
        q = q.where(Sale.channel == channel)
    if status:
        q = q.where(Sale.status == status)
    if search:
        like = f"%{search.strip()}%"
        q = q.where(or_(Sale.invoice_no.ilike(like), Customer.name.ilike(like), Customer.phone.like(like)))
    return q


@router.get("")
def list_sales(outlet_id: int | None = None, start: date | None = None, end: date | None = None,
               payment_method: str | None = None, channel: str | None = None, status: str | None = None,
               search: str | None = None, page: int = 1, page_size: int = Query(50, le=500),
               user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = _filtered(user, outlet_id, start, end, payment_method, channel, status, search)
    rows, total = paginate(db, q.order_by(Sale.sold_at.desc(), Sale.id.desc()), page, page_size)
    sub = q.with_only_columns(Sale.total, Sale.status).order_by(None).subquery()
    agg = db.execute(select(func.coalesce(func.sum(sub.c.total), 0), func.count()).where(sub.c.status == "completed")).one()
    resp = page_response([sale_dict(r[0]) for r in rows], total, page, page_size)
    resp["summary"] = {"revenue": round(agg[0], 2), "orders": agg[1],
                       "avg_bill": round(agg[0] / agg[1], 2) if agg[1] else 0}
    return resp


@router.get("/export")
def export_sales(outlet_id: int | None = None, start: date | None = None, end: date | None = None,
                 user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Line-level export in the same format as the sales import template."""
    if not start or not end:
        end = end or date.today()
        start = start or end - timedelta(days=30)
    if (end - start).days > 400:
        raise HTTPException(400, "Export at most ~13 months at a time")
    outlet_ids = scoped_outlet_ids(user, outlet_id)
    q = select(Sale.invoice_no, Sale.sold_at, Outlet.code, Product.sku, SaleItem.quantity, SaleItem.unit_price,
               SaleItem.discount, Sale.payment_method, Sale.channel, Customer.phone, Customer.name, SaleItem.line_total).join(
        SaleItem, SaleItem.sale_id == Sale.id).join(Outlet, Outlet.id == Sale.outlet_id).join(
        Product, Product.id == SaleItem.product_id).outerjoin(Customer, Customer.id == Sale.customer_id).where(
        Sale.status == "completed", Sale.sale_date >= start, Sale.sale_date <= end).order_by(Sale.sold_at)
    if outlet_ids:
        q = q.where(Sale.outlet_id.in_(outlet_ids))
    rows = ([inv, ts.date().isoformat(), ts.strftime("%H:%M"), oc, sku, qty, price, disc, pm, ch, ph or "", cn or "", lt]
            for inv, ts, oc, sku, qty, price, disc, pm, ch, ph, cn, lt in db.execute(q))
    return csv_response(f"sales_{start}_{end}.csv",
                        ["invoice_no", "date", "time", "outlet_code", "sku", "quantity", "unit_price", "discount",
                         "payment_method", "channel", "customer_phone", "customer_name", "line_total"], rows)


@router.get("/{sale_id}")
def get_sale(sale_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = get_or_404(db, Sale, sale_id, "Sale")
    ensure_outlet_access(user, s.outlet_id)
    return sale_dict(s, detail=True)


@router.post("", status_code=201)
def record_sale(body: SaleIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_outlet_access(user, body.outlet_id)
    sold_at = body.sold_at.replace(tzinfo=None) if body.sold_at else None
    if sold_at and user.role == "staff" and sold_at.date() < date.today() - timedelta(days=1):
        raise HTTPException(403, "Staff can only record sales for today or yesterday")
    sale = create_sale(db, SaleInput(
        outlet_id=body.outlet_id, sold_at=sold_at, payment_method=body.payment_method, channel=body.channel,
        customer_id=body.customer_id, customer_phone=body.customer_phone, customer_name=body.customer_name,
        bill_discount=body.bill_discount, notes=body.notes,
        lines=[LineInput(i.product_id, i.quantity, i.unit_price, i.discount) for i in body.items]), user, "manual")
    F.clear_cache()
    return sale_dict(sale, detail=True)


@router.post("/{sale_id}/void")
def void(sale_id: int, body: VoidIn, user: User = Depends(require_manager), db: Session = Depends(get_db)):
    s = get_or_404(db, Sale, sale_id, "Sale")
    ensure_outlet_access(user, s.outlet_id)
    void_sale(db, s, user, body.reason)
    F.clear_cache()
    return sale_dict(s, detail=True)

