"""
Alerts API Router - Alert Management and Monitoring

Provides endpoints for:
- Listing alerts with filtering and pagination
- Acknowledging alerts
- Getting alert summary for dashboard badges
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import Session

from app.core.data_isolation import OutletDataAccess

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=dict)
async def get_alerts(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    alert_type: Optional[AlertType] = Query(None, description="Filter by alert type"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledged status"),
    date_from: Optional[datetime] = Query(None, description="Filter alerts from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter alerts to this date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get paginated list of alerts for user's outlet scope.
    
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20, max: 100)
    - **alert_type**: Filter by alert type
    - **severity**: Filter by severity level
    - **acknowledged**: Filter by acknowledged status
    - **date_from**: Filter alerts created after this date
    - **date_to**: Filter alerts created before this date
    """
    
    # Build base query with access control
    stmt = select(Alert)

    # Apply outlet access control using the data isolation utility
    stmt = OutletDataAccess.apply_outlet_filter_select(stmt, current_user, 'outlet_id')
    
    # Apply filters
    if alert_type:
        stmt = stmt.where(Alert.alert_type == alert_type)
    
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    
    if acknowledged is not None:
        stmt = stmt.where(Alert.acknowledged == acknowledged)
    
    if date_from:
        stmt = stmt.where(Alert.created_at >= date_from)
    
    if date_to:
        stmt = stmt.where(Alert.created_at <= date_to)
    
    # Get total count
    count_stmt = stmt.with_only_columns(func.count(Alert.id))
    total_count = db.execute(count_stmt).scalar()
    
    # Apply pagination and ordering
    stmt = stmt.order_by(desc(Alert.created_at))
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    
    alerts = db.execute(stmt).scalars().all()
    
    # Convert to dict format
    alert_list = []
    for alert in alerts:
        alert_dict = {
            "id": alert.id,
            "outlet_id": alert.outlet_id,
            "product_id": alert.product_id,
            "alert_type": alert.alert_type.value,
            "severity": alert.severity.value,
            "message": alert.message,
            "acknowledged": alert.acknowledged,
            "acknowledged_by": alert.acknowledged_by,
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "notification_sent_at": alert.notification_sent_at.isoformat() if alert.notification_sent_at else None,
            "created_at": alert.created_at.isoformat(),
            "updated_at": alert.updated_at.isoformat(),
        }
        alert_list.append(alert_dict)
    
    return {
        "alerts": alert_list,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_count": total_count,
            "total_pages": (total_count + per_page - 1) // per_page,
        },
    }


@router.post("/{alert_id}/acknowledge", response_model=dict)
async def acknowledge_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Mark an alert as acknowledged by the current user.
    
    - **alert_id**: ID of the alert to acknowledge
    """
    
    # Get the alert
    alert = db.execute(select(Alert).where(Alert.id == alert_id)).scalar()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Check access control
    if current_user.role not in ["superadmin", "area_manager"]:
        if alert.outlet_id != current_user.outlet_id:
            raise HTTPException(status_code=403, detail="Access denied to this alert")
    elif current_user.role == "area_manager":
        # Check if alert's outlet is in user's area
        outlet = db.execute(select(Outlet).where(Outlet.id == alert.outlet_id)).scalar()
        if not outlet or outlet.area_id != current_user.area_id:
            raise HTTPException(status_code=403, detail="Access denied to this alert")
    
    # Check if already acknowledged
    if alert.acknowledged:
        raise HTTPException(status_code=400, detail="Alert is already acknowledged")
    
    # Acknowledge the alert
    alert.acknowledged = True
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    alert.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Alert acknowledged successfully",
        "alert_id": alert_id,
        "acknowledged_by": current_user.email,
        "acknowledged_at": alert.acknowledged_at.isoformat(),
    }


@router.get("/summary", response_model=dict)
async def get_alerts_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get alert summary with counts by severity and type for dashboard badges.
    
    Returns counts for:
    - Total unacknowledged alerts
    - Counts by severity (critical, high, medium, low)
    - Counts by type (stockout, low_stock, expiry_risk, sales_anomaly, forecast_deviation, supplier_delay)
    """
    
    # Build base query with access control
    base_stmt = select(Alert)
    
    if current_user.role not in ["superadmin", "area_manager"]:
        base_stmt = base_stmt.where(Alert.outlet_id == current_user.outlet_id)
    elif current_user.role == "area_manager":
        base_stmt = base_stmt.where(Alert.outlet_id.in_(
            select(Outlet.id).where(Outlet.area_id == current_user.area_id)
        ))
    
    # Get unacknowledged alerts only
    stmt = base_stmt.where(Alert.acknowledged == False)
    
    # Count by severity
    severity_counts = {}
    for severity in AlertSeverity:
        count_stmt = stmt.with_only_columns(func.count(Alert.id)).where(Alert.severity == severity)
        severity_counts[severity.value] = db.execute(count_stmt).scalar()
    
    # Count by type
    type_counts = {}
    for alert_type in AlertType:
        count_stmt = stmt.with_only_columns(func.count(Alert.id)).where(Alert.alert_type == alert_type)
        type_counts[alert_type.value] = db.execute(count_stmt).scalar()
    
    # Total unacknowledged
    total_stmt = stmt.with_only_columns(func.count(Alert.id))
    total_unacknowledged = db.execute(total_stmt).scalar()
    
    # Critical and high severity counts for badges
    critical_high_count = severity_counts.get('critical', 0) + severity_counts.get('high', 0)
    
    return {
        "total_unacknowledged": total_unacknowledged,
        "critical_high_count": critical_high_count,
        "severity_counts": severity_counts,
        "type_counts": type_counts,
        "last_updated": datetime.utcnow().isoformat(),
    }