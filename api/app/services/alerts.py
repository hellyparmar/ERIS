"""Business alerts computed live from the data (nothing to configure or keep in sync)."""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import InventoryItem, Outlet, Product, PurchaseOrder, Sale
from app.services import analytics as A
from app.services.holidays import upcoming_events


def compute_alerts(db: Session, outlet_ids: list[int] | None = None) -> list[dict]:
    alerts: list[dict] = []
    anchor = A.anchor_date(db)
    names = A.outlet_names(db)

    # 1. Stock
    q = select(InventoryItem.outlet_id, Product.name, InventoryItem.quantity, InventoryItem.reorder_level).join(
        Product, Product.id == InventoryItem.product_id).where(
        Product.is_active.is_(True), InventoryItem.reorder_level > 0,
        InventoryItem.quantity <= InventoryItem.reorder_level)
    if outlet_ids:
        q = q.where(InventoryItem.outlet_id.in_(outlet_ids))
    rows = db.execute(q).all()
    out = [r for r in rows if r.quantity <= 0]
    low = [r for r in rows if r.quantity > 0]
    if out:
        sample = ", ".join(f"{r.name} ({names.get(r.outlet_id)})" for r in out[:3])
        alerts.append({"id": "stock-out", "severity": "critical", "type": "inventory",
                       "title": f"{len(out)} item{'s' if len(out) > 1 else ''} out of stock",
                       "message": f"{sample}{' and more' if len(out) > 3 else ''}. Lost sales are likely until restocked.",
                       "link": "/inventory?status=out_of_stock"})
    if low:
        alerts.append({"id": "stock-low", "severity": "warning", "type": "inventory",
                       "title": f"{len(low)} item{'s' if len(low) > 1 else ''} below reorder level",
                       "message": "Review the reorder suggestions to raise purchase orders in one click.",
                       "link": "/inventory?tab=reorder"})

    # 2. Overdue purchase orders
    q = select(func.count(PurchaseOrder.id)).where(PurchaseOrder.status == "ordered",
                                                   PurchaseOrder.expected_date < date.today())
    if outlet_ids:
        q = q.where(PurchaseOrder.outlet_id.in_(outlet_ids))
    overdue = db.scalar(q) or 0
    if overdue:
        alerts.append({"id": "po-overdue", "severity": "warning", "type": "purchasing",
                       "title": f"{overdue} purchase order{'s' if overdue > 1 else ''} overdue",
                       "message": "Deliveries are past their expected date - follow up with the suppliers.",
                       "link": "/suppliers?tab=orders"})

    # 3. Outlet revenue trend: last 7 days vs previous 7 days
    week = A.DateRange(anchor - timedelta(days=6), anchor)
    for o in A.outlet_performance(db, week, outlet_ids):
        if o["change_pct"] is not None and o["change_pct"] <= -15 and o["previous_revenue"] > 0:
            alerts.append({"id": f"outlet-drop-{o['outlet_id']}", "severity": "warning", "type": "sales",
                           "title": f"{o['name']} revenue down {abs(o['change_pct']):.0f}%",
                           "message": "Last 7 days compared with the 7 days before. Check footfall, staffing and stock.",
                           "link": f"/analytics?outlet={o['outlet_id']}"})
        elif o["change_pct"] is not None and o["change_pct"] >= 20:
            alerts.append({"id": f"outlet-up-{o['outlet_id']}", "severity": "info", "type": "sales",
                           "title": f"{o['name']} revenue up {o['change_pct']:.0f}%",
                           "message": "Last 7 days compared with the 7 days before. Make sure stock keeps up.",
                           "link": f"/analytics?outlet={o['outlet_id']}"})

    # 4. Latest day vs typical same weekday (last 4 weeks)
    q = select(Sale.sale_date, func.sum(Sale.total)).where(
        A.COMPLETED, Sale.sale_date.in_([anchor - timedelta(days=7 * k) for k in range(0, 5)]))
    if outlet_ids:
        q = q.where(Sale.outlet_id.in_(outlet_ids))
    by_day = dict(db.execute(q.group_by(Sale.sale_date)).all())
    latest = by_day.get(anchor, 0)
    past = [by_day.get(anchor - timedelta(days=7 * k), 0) for k in range(1, 5)]
    past = [p for p in past if p > 0]
    if past and latest:
        typical = sum(past) / len(past)
        dev = (latest - typical) / typical * 100
        if abs(dev) >= 25:
            alerts.append({"id": "day-anomaly", "severity": "warning" if dev < 0 else "info", "type": "sales",
                           "title": f"Unusual sales on {anchor:%a %d %b}: {dev:+.0f}%",
                           "message": f"Revenue was {'below' if dev < 0 else 'above'} the typical {anchor:%A}.",
                           "link": "/sales"})

    # 5. Upcoming festivals
    for ev in upcoming_events(anchor + timedelta(days=1), 21):
        alerts.append({"id": f"event-{ev['name']}-{ev['date']}", "severity": "info", "type": "planning",
                       "title": f"{ev['name']} in {ev['days_away']} days",
                       "message": "Festival demand is expected - check the forecast and stock up on festive items.",
                       "link": "/forecasts"})

    # 6. Inactive outlets with stock
    if not outlet_ids:
        inactive = db.scalar(select(func.count(Outlet.id)).where(Outlet.is_active.is_(False))) or 0
        if inactive:
            alerts.append({"id": "outlets-inactive", "severity": "info", "type": "outlets",
                           "title": f"{inactive} outlet{'s' if inactive > 1 else ''} marked inactive",
                           "message": "Inactive outlets are excluded from new sales.", "link": "/outlets"})

    order = {"critical": 0, "warning": 1, "info": 2}
    return sorted(alerts, key=lambda a: order[a["severity"]])
