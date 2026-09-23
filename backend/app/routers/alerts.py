from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, select
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models import Alert, Inventory, Product, AlertSeverity, AlertType
from app.models.users import User
from app.api.deps import get_current_active_user, get_outlet_scope
from app.core.data_isolation import require_outlet_access

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/list")
async def get_alerts(
    severity: Optional[str] = Query(None, pattern="^(critical|warning|medium|high|info)$"),
    category: Optional[str] = None,  # Note: mapped to alert_type in DB
    unread_only: bool = False,
    outlet_id: Optional[int] = Query(None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get system alerts from the database with outlet scoping"""
    from sqlalchemy import select, func, or_
    from app.models import Product, Inventory
    
    allowed_outlets = get_outlet_scope(current_user, db)
    
    # Base query joining Alert, Product, and Inventory
    query = select(Alert, Product, Inventory).outerjoin(
        Product, Alert.product_id == Product.id
    ).outerjoin(
        Inventory, and_(Product.id == Inventory.product_id, Alert.outlet_id == Inventory.outlet_id)
    )
    
    # Outlet filtering
    if allowed_outlets:
        if outlet_id:
            if not require_outlet_access(current_user, outlet_id):
                raise HTTPException(status_code=403, detail="Access denied to this outlet")
            query = query.where(Alert.outlet_id == outlet_id)
        else:
            query = query.where(Alert.outlet_id.in_(allowed_outlets))
    elif outlet_id:
        query = query.where(Alert.outlet_id == outlet_id)
        
    # Filters
    if severity:
        query = query.where(Alert.severity == severity)
        
    if category:
        query = query.where(Alert.alert_type == category)
        
    if unread_only:
        query = query.where(Alert.is_acknowledged == False)
        
    # Total count for pagination
    total_query = select(func.count()).select_from(query.subquery())
    total = db.execute(total_query).scalar() or 0
    
    # Pagination
    total_pages = (total + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    
    query = query.order_by(Alert.created_at.desc()).offset(start_idx).limit(per_page)
    results = db.execute(query).all()
    
    # Format for response
    formatted_results = []
    for alert, product, inventory in results:
        formatted_results.append({
            'id': str(alert.id),
            'severity': alert.severity.value,
            'category': alert.alert_type.value,
            'alert_type': alert.alert_type.value,
            'title': f"{alert.alert_type.value.replace('_', ' ').title()}: {product.name if product else 'System'}",
            'message': alert.message,
            'created_at': alert.created_at.isoformat() if alert.created_at else None,
            'is_acknowledged': alert.is_acknowledged,
            'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            'product_id': str(alert.product_id) if alert.product_id else None,
            'product_name': product.name if product else None,
            'outlet_id': alert.outlet_id,
            'current_stock': inventory.quantity if inventory else 0,
            'reorder_level': product.reorder_level if product else 0
        })
        
    return {
        "success": True,
        "data": {
            "items": formatted_results,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages
            },
            "filters_applied": {
                "severity": severity,
                "category": category,
                "unread_only": unread_only
            }
        }
    }

@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark an alert as acknowledged"""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        return {"success": False, "error": "Alert not found"}
    if getattr(alert, 'outlet_id', None) and not require_outlet_access(current_user, alert.outlet_id):
        raise HTTPException(status_code=403, detail="Access denied to this alert")
    
    alert.is_acknowledged = True
    alert.acknowledged_at = datetime.now()
    alert.acknowledged_by = current_user.id
    db.commit()
    
    return {"success": True, "message": "Alert acknowledged"}

@router.post("/generate-inventory-alerts")
async def generate_inventory_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate alerts for low stock, out of stock, and overstocked items
    This can be called periodically or triggered manually
    """
    alerts_created = []
    
    # Find low stock items
    low_stock_items = db.query(Inventory, Product).join(
        Product, Inventory.product_id == Product.id
    ).filter(
        and_(
            Inventory.current_stock > 0,
            Inventory.current_stock < Inventory.reorder_point
        )
    ).all()
    
    for inventory, product in low_stock_items:
        # Check if alert already exists for this product
        result = await db.execute(select(Alert).where(and_(
                Alert.product_id == product.id,
                Alert.alert_type == AlertType.low_stock,
                Alert.is_acknowledged == False
            )))
        existing = result.scalar_one_or_none()
        if not existing:
            alert = Alert(
                severity=AlertSeverity.warning,
                alert_type=AlertType.low_stock,
                title=f"Low Stock: {product.name}",
                message=f"{product.name} is running low ({inventory.current_stock} units remaining, reorder at {inventory.reorder_point})",
                product_id=product.id
            )
            db.add(alert)
            alerts_created.append(alert.title)
    
    # Find out of stock items
    out_of_stock = db.query(Inventory, Product).join(
        Product, Inventory.product_id == Product.id
    ).filter(Inventory.current_stock == 0).all()
    
    for inventory, product in out_of_stock:
        result = await db.execute(select(Alert).where(and_(
                Alert.product_id == product.id,
                Alert.alert_type == AlertType.stockout,
                Alert.severity == AlertSeverity.critical,
                Alert.is_acknowledged == False
            )))
        existing = result.scalar_one_or_none()
        if not existing:
            alert = Alert(
                severity=AlertSeverity.critical,
                alert_type=AlertType.stockout,
                title=f"Out of Stock: {product.name}",
                message=f"{product.name} is completely out of stock. Immediate reorder required.",
                product_id=product.id
            )
            db.add(alert)
            alerts_created.append(alert.title)
    
    db.commit()
    
    return {
        "success": True,
        "alerts_created": len(alerts_created),
        "details": alerts_created
    }
