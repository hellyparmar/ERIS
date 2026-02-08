"""
Alerts Router - System Alerts and Notifications
Generates alerts from inventory, sales, and system events
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from api.db.database import get_db
from api.db.models import Alert, Inventory, Product, AlertSeverity

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])

@router.get("/list")
async def get_alerts(
    severity: Optional[str] = Query(None, regex="^(critical|warning|info)$"),
    category: Optional[str] = None,
    unread_only: bool = False,
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """Get system alerts with filtering"""
    query = db.query(Alert).order_by(Alert.created_at.desc())
    
    if severity:
        query = query.filter(Alert.severity == AlertSeverity[severity.upper()])
    if category:
        query = query.filter(Alert.category == category)
    if unread_only:
        query = query.filter(Alert.is_acknowledged == False)
    
    alerts = query.limit(limit).all()
    
    result = []
    for alert in alerts:
        result.append({
            "id": alert.id,
            "severity": alert.severity.value,
            "category": alert.category,
            "title": alert.title,
            "message": alert.message,
            "is_acknowledged": alert.is_acknowledged,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
            "related_product_id": alert.related_product_id
        })
    
    return {"success": True, "data": result, "count": len(result)}

@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Mark an alert as acknowledged"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        return {"success": False, "error": "Alert not found"}
    
    alert.is_acknowledged = True
    alert.acknowledged_at = datetime.now()
    db.commit()
    
    return {"success": True, "message": "Alert acknowledged"}

@router.post("/generate-inventory-alerts")
async def generate_inventory_alerts(db: Session = Depends(get_db)):
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
        existing = db.query(Alert).filter(
            and_(
                Alert.related_product_id == product.id,
                Alert.category == "stock",
                Alert.is_acknowledged == False
            )
        ).first()
        
        if not existing:
            alert = Alert(
                severity=AlertSeverity.WARNING,
                category="stock",
                title=f"Low Stock: {product.name}",
                message=f"{product.name} is running low ({inventory.current_stock} units remaining, reorder at {inventory.reorder_point})",
                related_product_id=product.id
            )
            db.add(alert)
            alerts_created.append(alert.title)
    
    # Find out of stock items
    out_of_stock = db.query(Inventory, Product).join(
        Product, Inventory.product_id == Product.id
    ).filter(Inventory.current_stock == 0).all()
    
    for inventory, product in out_of_stock:
        existing = db.query(Alert).filter(
            and_(
                Alert.related_product_id == product.id,
                Alert.category == "stock",
                Alert.severity == AlertSeverity.CRITICAL,
                Alert.is_acknowledged == False
            )
        ).first()
        
        if not existing:
            alert = Alert(
                severity=AlertSeverity.CRITICAL,
                category="stock",
                title=f"Out of Stock: {product.name}",
                message=f"{product.name} is completely out of stock. Immediate reorder required.",
                related_product_id=product.id
            )
            db.add(alert)
            alerts_created.append(alert.title)
    
    db.commit()
    
    return {
        "success": True,
        "alerts_created": len(alerts_created),
        "details": alerts_created
    }
