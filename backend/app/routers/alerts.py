"""Outlet-scoped inventory and anomaly alerts."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_outlet_scope, require_role
from app.database import get_db_sync_dependency
from app.models import Alert, AlertSeverity, AlertType, Inventory, Product
from app.models.users import User


router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/list")
def get_alerts(
    severity: Optional[AlertSeverity] = None,
    category: Optional[AlertType] = None,
    unread_only: bool = False,
    acknowledged: Optional[bool] = None,
    outlet_id: Optional[int] = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_sync_dependency),
):
    allowed_outlets = get_outlet_scope(current_user, db)
    if outlet_id is not None:
        if outlet_id not in allowed_outlets:
            raise HTTPException(status_code=403, detail="Access denied to this outlet")
        allowed_outlets = [outlet_id]
    if not allowed_outlets:
        allowed_outlets = [-1]

    query = (
        select(Alert, Product, Inventory)
        .outerjoin(Product, Alert.product_id == Product.id)
        .outerjoin(
            Inventory,
            and_(Product.id == Inventory.product_id, Alert.outlet_id == Inventory.outlet_id),
        )
        .where(Alert.outlet_id.in_(allowed_outlets))
    )
    if severity is not None:
        query = query.where(Alert.severity == severity)
    if category is not None:
        query = query.where(Alert.alert_type == category)
    if unread_only:
        query = query.where(Alert.is_acknowledged.is_(False))
    elif acknowledged is not None:
        query = query.where(Alert.is_acknowledged.is_(acknowledged))

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
    rows = db.execute(query.order_by(Alert.created_at.desc()).offset((page - 1) * per_page).limit(per_page)).all()

    items = [
        {
            "id": str(alert.id),
            "severity": alert.severity.value,
            "alert_type": alert.alert_type.value,
            "title": f"{alert.alert_type.value.replace('_', ' ').title()}: {product.name if product else 'System'}",
            "message": alert.message,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
            "is_acknowledged": alert.is_acknowledged,
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            "product_id": str(alert.product_id) if alert.product_id else None,
            "product_name": product.name if product else None,
            "outlet_id": alert.outlet_id,
            "current_stock": inventory.current_stock if inventory else None,
            "reorder_level": product.reorder_level if product else None,
        }
        for alert, product, inventory in rows
    ]

    return {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        },
    }


@router.patch("/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: UUID,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db_sync_dependency),
):
    alert = db.execute(select(Alert).where(Alert.id == alert_id)).scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.outlet_id not in get_outlet_scope(current_user, db):
        raise HTTPException(status_code=403, detail="Access denied to this alert")

    alert.is_acknowledged = True
    alert.acknowledged_at = datetime.now(timezone.utc)
    alert.acknowledged_by = current_user.id
    db.commit()
    return {"success": True, "message": "Alert acknowledged"}


@router.post("/generate-inventory-alerts")
def generate_inventory_alerts(
    db: Session = Depends(get_db_sync_dependency),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Create missing low-stock/stockout alerts for accessible outlets."""
    allowed_outlets = get_outlet_scope(current_user, db)
    if not allowed_outlets:
        return {"success": True, "alerts_created": 0}

    rows = db.execute(
        select(Inventory, Product)
        .join(Product, Inventory.product_id == Product.id)
        .where(
            Inventory.outlet_id.in_(allowed_outlets),
            Inventory.current_stock <= Product.reorder_level,
        )
    ).all()

    created = 0
    for inventory, product in rows:
        alert_type = AlertType.stockout if inventory.current_stock == 0 else AlertType.low_stock
        exists = db.execute(
            select(Alert.id).where(
                Alert.outlet_id == inventory.outlet_id,
                Alert.product_id == product.id,
                Alert.alert_type == alert_type,
                Alert.is_acknowledged.is_(False),
            )
        ).first()
        if exists:
            continue
        severity = AlertSeverity.critical if inventory.current_stock == 0 else AlertSeverity.high
        db.add(
            Alert(
                outlet_id=inventory.outlet_id,
                product_id=product.id,
                alert_type=alert_type,
                severity=severity,
                message=(
                    f"{product.name} is out of stock."
                    if inventory.current_stock == 0
                    else f"{product.name} has {inventory.current_stock} units left; reorder level is {product.reorder_level}."
                ),
            )
        )
        created += 1
    db.commit()
    return {"success": True, "alerts_created": created}
