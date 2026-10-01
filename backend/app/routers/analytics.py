"""Outlet-scoped, database-backed analytics endpoints."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_outlet_scope
from app.database import get_db_sync_dependency
from app.middleware.rate_limiter import limiter
from app.models.alert import Alert
from app.models.inventory import Inventory
from app.models.commerce import Product, ProductCategory, Sale, SaleItem
from app.models.outlet import Outlet
from app.models.users import User
from app.schemas.analytics import AlertsResponse, MetricData


router = APIRouter(prefix="/analytics", tags=["Analytics/Dashboard"])


def _outlets(current_user: User, db: Session) -> list[int]:
    return get_outlet_scope(current_user, db)


def _period_days(period: str) -> int:
    return {"7d": 7, "14d": 14, "30d": 30, "90d": 90, "365d": 365}.get(period, 30)


def _sale_scope(db: Session, current_user: User, outlet_ids: list[int]):
    query = db.query(Sale).filter(Sale.organization_id == current_user.organization_id)
    return query.filter(Sale.outlet_id.in_(outlet_ids)) if outlet_ids else query.filter(False)


@router.get("/metrics", response_model=MetricData)
@limiter.limit("1000/minute")
async def get_metrics(
    request: Request,
    db: Session = Depends(get_db_sync_dependency),
    current_user: User = Depends(get_current_user),
):
    outlet_ids = _outlets(current_user, db)
    sales = _sale_scope(db, current_user, outlet_ids)
    total_revenue = sales.with_entities(func.sum(Sale.total_amount)).scalar() or 0
    since = datetime.now(timezone.utc) - timedelta(days=30)
    recent_revenue = sales.filter(Sale.sale_date >= since).with_entities(func.sum(Sale.total_amount)).scalar() or 0
    inventory_value = 0
    stockout_risk = 0
    alert_count = 0
    critical_count = 0
    if outlet_ids:
        inventory_value = (
            db.query(func.sum(Product.cost_price * Inventory.current_stock))
            .join(Inventory, Inventory.product_id == Product.id)
            .filter(
                Product.organization_id == current_user.organization_id,
                Inventory.outlet_id.in_(outlet_ids),
            )
            .scalar()
            or 0
        )
        stockout_risk = (
            db.query(func.count(Inventory.id))
            .join(Product)
            .filter(
                Product.organization_id == current_user.organization_id,
                Inventory.outlet_id.in_(outlet_ids),
                Inventory.current_stock <= Product.reorder_level,
            )
            .scalar()
            or 0
        )
        alert_count = (
            db.query(func.count(Alert.id))
            .filter(Alert.outlet_id.in_(outlet_ids), Alert.is_acknowledged.is_(False))
            .scalar()
            or 0
        )
        critical_count = (
            db.query(func.count(Alert.id))
            .filter(Alert.outlet_id.in_(outlet_ids), Alert.is_acknowledged.is_(False), Alert.severity == "critical")
            .scalar()
            or 0
        )
    return {
        "totalRevenue": float(total_revenue),
        "avgDailySales": float(recent_revenue) / 30,
        "inventoryValue": float(inventory_value),
        "stockoutRisk": float(stockout_risk),
        "alertCount": int(alert_count),
        "criticalAlertCount": int(critical_count),
    }


@router.get("/alerts", response_model=AlertsResponse)
@limiter.limit("1000/minute")
async def get_alerts(
    request: Request,
    severity: str = Query("all", pattern="^(all|critical|high|medium|low)$"),
    db: Session = Depends(get_db_sync_dependency),
    current_user: User = Depends(get_current_user),
):
    outlet_ids = _outlets(current_user, db)
    query = (
        db.query(Alert).filter(Alert.outlet_id.in_(outlet_ids), Alert.is_acknowledged.is_(False))
        if outlet_ids
        else db.query(Alert).filter(False)
    )
    if severity != "all":
        query = query.filter(Alert.severity == severity)
    alerts = query.order_by(Alert.created_at.desc()).limit(50).all()
    return {
        "alerts": [
            {
                "id": str(alert.id),
                "severity": alert.severity.value if hasattr(alert.severity, "value") else str(alert.severity),
                "message": alert.message,
                "timestamp": alert.created_at.isoformat() if alert.created_at else "",
            }
            for alert in alerts
        ],
        "total": len(alerts),
    }


@router.get("/dashboard/realtime")
def get_dashboard_realtime(
    db: Session = Depends(get_db_sync_dependency),
    current_user: User = Depends(get_current_user),
):
    outlet_ids = _outlets(current_user, db)
    sales = _sale_scope(db, current_user, outlet_ids)
    today = datetime.now(timezone.utc).date()
    total_revenue = sales.with_entities(func.sum(Sale.total_amount)).scalar() or 0
    total_orders = sales.count()
    today_sales = sales.filter(func.date(Sale.sale_date) == today)
    today_revenue = today_sales.with_entities(func.sum(Sale.total_amount)).scalar() or 0
    recent = sales.options(selectinload(Sale.customer)).order_by(Sale.sale_date.desc()).limit(10).all()
    return {
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "today_revenue": float(today_revenue),
        "active_orders": today_sales.count(),
        "avg_order_value": round(float(total_revenue) / total_orders, 2) if total_orders else 0,
        "data_source": "database",
        "recent_transactions": [
            {
                "id": sale.sale_number or str(sale.id),
                "customer": sale.customer.name if sale.customer else "Walk-in Customer",
                "amount": float(sale.total_amount or 0),
                "status": sale.payment_status,
                "timestamp": sale.sale_date.isoformat() if sale.sale_date else "",
            }
            for sale in recent
        ],
    }


@router.get("/dashboard/summary")
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_sync_dependency),
) -> Any:
    outlet_ids = _outlets(current_user, db)
    sales = _sale_scope(db, current_user, outlet_ids)
    today = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    previous_week = today - timedelta(days=14)

    def revenue_since(start_date, before=None):
        query = sales.filter(func.date(Sale.sale_date) >= start_date)
        if before is not None:
            query = query.filter(func.date(Sale.sale_date) < before)
        return float(query.with_entities(func.sum(Sale.total_amount)).scalar() or 0)

    revenue_today = revenue_since(today)
    revenue_week = revenue_since(week_ago)
    revenue_month = revenue_since(month_ago)
    previous_revenue = revenue_since(previous_week, week_ago)
    transactions_today = sales.filter(func.date(Sale.sale_date) == today).count()
    low_stock = 0
    if outlet_ids:
        low_stock = (
            db.query(func.count(Inventory.id))
            .join(Product)
            .filter(Inventory.outlet_id.in_(outlet_ids), Inventory.current_stock <= Product.reorder_level)
            .scalar()
            or 0
        )
    change = ((revenue_week - previous_revenue) / previous_revenue * 100) if previous_revenue else 0
    return {
        "total_revenue_today": revenue_today,
        "total_revenue_this_week": revenue_week,
        "total_revenue_this_month": revenue_month,
        "total_transactions_today": transactions_today,
        "low_stock_alerts_count": int(low_stock),
        "revenue_change_percent": round(change, 1),
        "summary_text": f"{transactions_today} transactions today",
    }


@router.get("/dashboard/revenue-trend")
def get_revenue_trend(
    days: Optional[int] = Query(30, ge=1, le=365),
    period: Optional[str] = Query(None, pattern="^(7d|30d|90d|365d)$"),
    outlet_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_sync_dependency),
) -> Any:
    allowed = _outlets(current_user, db)
    if outlet_id is not None and outlet_id not in allowed:
        raise HTTPException(status_code=403, detail="Access denied to this outlet")
    scoped = [outlet_id] if outlet_id is not None else allowed
    since = datetime.now(timezone.utc).date() - timedelta(days=_period_days(period) if period else days or 30)
    rows = (
        _sale_scope(db, current_user, scoped)
        .filter(func.date(Sale.sale_date) >= since)
        .with_entities(func.date(Sale.sale_date).label("date"), func.sum(Sale.total_amount).label("revenue"))
        .group_by(func.date(Sale.sale_date))
        .order_by(func.date(Sale.sale_date))
        .all()
    )
    return [{"date": str(row.date), "revenue": float(row.revenue or 0)} for row in rows]


@router.get("/dashboard/category-breakdown")
def get_category_breakdown(
    period: str = Query("30d", pattern="^(7d|30d|90d|365d)$"),
    outlet_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_sync_dependency),
) -> Any:
    allowed = _outlets(current_user, db)
    if outlet_id is not None and outlet_id not in allowed:
        raise HTTPException(status_code=403, detail="Access denied to this outlet")
    scoped = [outlet_id] if outlet_id is not None else allowed
    since = datetime.now(timezone.utc).date() - timedelta(days=_period_days(period))
    if not scoped:
        rows = []
    else:
        rows = (
            db.query(
                ProductCategory.name.label("category"),
                func.sum(SaleItem.line_total).label("revenue"),
                func.sum(SaleItem.quantity).label("quantity"),
                func.count(func.distinct(Sale.id)).label("transactions"),
            )
            .join(Product, Product.category_id == ProductCategory.id)
            .join(SaleItem, SaleItem.product_id == Product.id)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .filter(
                Sale.organization_id == current_user.organization_id,
                Sale.outlet_id.in_(scoped),
                func.date(Sale.sale_date) >= since,
            )
            .group_by(ProductCategory.name)
            .order_by(func.sum(SaleItem.line_total).desc())
            .all()
        )
    total = sum(float(row.revenue or 0) for row in rows)
    return {
        "period": period,
        "outlet_id": outlet_id,
        "total_revenue": total,
        "data": [
            {
                "category": row.category or "Other",
                "revenue": float(row.revenue or 0),
                "percentage": float(row.revenue or 0) / total * 100 if total else 0,
                "quantity": int(row.quantity or 0),
                "transactions": int(row.transactions or 0),
            }
            for row in rows
        ],
    }


@router.get("/dashboard/top-products")
def get_top_products(
    limit: int = Query(5, ge=1, le=50),
    period: str = Query("30d", pattern="^(7d|30d|90d|365d)$"),
    outlet_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_sync_dependency),
) -> Any:
    outlet_ids = _outlets(current_user, db)
    if not outlet_ids:
        return []
    if outlet_id is not None:
        if outlet_id not in outlet_ids:
            raise HTTPException(status_code=403, detail="Access denied to this outlet")
        outlet_ids = [outlet_id]
    since = datetime.now(timezone.utc).date() - timedelta(days=_period_days(period))
    rows = (
        db.query(
            Product.id,
            Product.name,
            Product.selling_price,
            ProductCategory.name.label("category"),
            func.sum(SaleItem.line_total).label("revenue"),
            func.sum(SaleItem.quantity).label("quantity"),
        )
        .join(SaleItem, SaleItem.product_id == Product.id)
        .join(Sale, Sale.id == SaleItem.sale_id)
        .outerjoin(ProductCategory, Product.category_id == ProductCategory.id)
        .filter(
            Sale.organization_id == current_user.organization_id,
            Sale.outlet_id.in_(outlet_ids),
            func.date(Sale.sale_date) >= since,
        )
        .group_by(Product.id, Product.name, Product.selling_price, ProductCategory.name)
        .order_by(func.sum(SaleItem.line_total).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "name": row.name,
            "unit_price": float(row.selling_price or 0),
            "category": row.category or "Other",
            "revenue": float(row.revenue or 0),
            "quantity_sold": int(row.quantity or 0),
        }
        for row in rows
    ]


@router.get("/dashboard/outlet-performance")
def get_outlet_performance(
    period: str = Query("30d", pattern="^(7d|14d|30d|90d|365d)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_sync_dependency),
) -> Any:
    outlet_ids = _outlets(current_user, db)
    if not outlet_ids:
        return []
    since = datetime.now(timezone.utc).date() - timedelta(days=_period_days(period))
    rows = (
        db.query(
            Outlet.id,
            Outlet.name,
            Outlet.city,
            func.coalesce(func.sum(Sale.total_amount), 0).label("revenue"),
            func.count(Sale.id).label("transactions"),
        )
        .outerjoin(Sale, (Sale.outlet_id == Outlet.id) & (func.date(Sale.sale_date) >= since))
        .filter(
            Outlet.id.in_(outlet_ids),
            Outlet.organization_id == current_user.organization_id,
            Outlet.is_active.is_(True),
        )
        .group_by(Outlet.id, Outlet.name, Outlet.city)
        .order_by(func.sum(Sale.total_amount).desc())
        .all()
    )
    return [
        {
            "outlet_id": row.id,
            "outlet_name": row.name,
            "city": row.city or "Unknown",
            "revenue": float(row.revenue or 0),
            "transactions": int(row.transactions or 0),
        }
        for row in rows
    ]
