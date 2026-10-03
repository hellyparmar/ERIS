from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import MAX_OUTLETS, InventoryItem, Organization, Outlet, Product, Sale, User, user_outlets
from app.routers.common import get_or_404
from app.schemas import OutletIn
from app.security import ensure_outlet_access, get_current_user, require_admin, scoped_outlet_ids
from app.services import analytics as A

router = APIRouter(prefix="/api/outlets", tags=["outlets"])


def outlet_dict(o: Outlet) -> dict:
    return {"id": o.id, "code": o.code, "name": o.name, "city": o.city, "state": o.state, "state_code": o.state_code,
            "address": o.address, "phone": o.phone,
            "manager_name": o.manager_name, "opened_on": o.opened_on.isoformat() if o.opened_on else None,
            "is_active": o.is_active}


@router.get("")
def list_outlets(with_stats: bool = False, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ids = scoped_outlet_ids(user)
    q = select(Outlet).order_by(Outlet.id)
    if ids:
        q = q.where(Outlet.id.in_(ids))
    outlets = db.scalars(q).all()
    out = [outlet_dict(o) for o in outlets]
    if with_stats and out:
        anchor = A.anchor_date(db)
        rng = A.DateRange(anchor - timedelta(days=29), anchor)
        perf = {p["outlet_id"]: p for p in A.outlet_performance(db, rng, ids)}
        stock = dict(db.execute(select(InventoryItem.outlet_id, func.sum(InventoryItem.quantity * Product.cost_price))
                                .join(Product, Product.id == InventoryItem.product_id)
                                .group_by(InventoryItem.outlet_id)).all())
        low = dict(db.execute(select(InventoryItem.outlet_id, func.count(InventoryItem.id)).where(
            InventoryItem.reorder_level > 0, InventoryItem.quantity <= InventoryItem.reorder_level).group_by(
            InventoryItem.outlet_id)).all())
        staff = dict(db.execute(select(user_outlets.c.outlet_id, func.count(User.id)).join(
            User, User.id == user_outlets.c.user_id).where(User.is_active.is_(True)).group_by(
            user_outlets.c.outlet_id)).all())
        for o in out:
            p = perf.get(o["id"], {})
            o["stats"] = {
                "revenue_30d": p.get("revenue", 0), "orders_30d": p.get("orders", 0),
                "avg_basket": p.get("avg_basket", 0), "change_pct": p.get("change_pct"),
                "margin_pct": p.get("margin_pct", 0), "share_pct": p.get("share_pct", 0),
                "stock_value": round(stock.get(o["id"], 0) or 0, 2), "low_stock_items": low.get(o["id"], 0),
                "users": staff.get(o["id"], 0),
            }
    return out


@router.get("/{outlet_id}")
def get_outlet(outlet_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_outlet_access(user, outlet_id)
    o = get_or_404(db, Outlet, outlet_id, "Outlet")
    anchor = A.anchor_date(db)
    rng = A.DateRange(anchor - timedelta(days=89), anchor)
    return {
        **outlet_dict(o),
        "kpis": A.kpis_with_comparison(db, A.DateRange(anchor - timedelta(days=29), anchor), [o.id]),
        "trend": A.revenue_series(db, rng, [o.id], "week"),
        "top_products": A.top_products(db, A.DateRange(anchor - timedelta(days=29), anchor), [o.id], 8),
        "categories": A.category_breakdown(db, A.DateRange(anchor - timedelta(days=29), anchor), [o.id]),
    }


@router.post("", status_code=201)
def create_outlet(body: OutletIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.scalar(select(Outlet.id).where(Outlet.code == body.code)):
        raise HTTPException(409, f"Outlet code {body.code} already exists")
    if (db.scalar(select(func.count(Outlet.id))) or 0) >= MAX_OUTLETS:
        raise HTTPException(400, f"ERIS supports up to {MAX_OUTLETS} outlets per organization")
    org = db.scalar(select(Organization))
    o = Outlet(**body.model_dump(), organization_id=org.id if org else None)
    db.add(o)
    db.flush()
    # Start every product at zero stock so the outlet appears in inventory immediately.
    for p in db.scalars(select(Product).where(Product.is_active.is_(True))).all():
        db.add(InventoryItem(outlet_id=o.id, product_id=p.id, quantity=0, reorder_level=p.reorder_level))
    db.commit()
    return outlet_dict(o)


@router.put("/{outlet_id}")
def update_outlet(outlet_id: int, body: OutletIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    o = get_or_404(db, Outlet, outlet_id, "Outlet")
    if body.code != o.code and db.scalar(select(Outlet.id).where(Outlet.code == body.code)):
        raise HTTPException(409, f"Outlet code {body.code} already exists")
    for k, v in body.model_dump().items():
        setattr(o, k, v)
    db.commit()
    return outlet_dict(o)


@router.delete("/{outlet_id}")
def delete_outlet(outlet_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    o = get_or_404(db, Outlet, outlet_id, "Outlet")
    if db.scalar(select(func.count(Sale.id)).where(Sale.outlet_id == o.id)):
        o.is_active = False
        db.commit()
        return {"ok": True, "deactivated": True,
                "message": "Outlet has sales history, so it was marked inactive instead of deleted."}
    db.delete(o)
    db.commit()
    return {"ok": True, "deleted": True}
