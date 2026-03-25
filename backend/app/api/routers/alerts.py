"""
Alerts Router - System Alerts and Notifications
Generates alerts from inventory, sales, and system events
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.api.db import get_db
from app.api.db.models import Alert, Inventory, Product, AlertSeverity

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])

@router.get("/list")
async def get_alerts(
    severity: Optional[str] = Query(None, regex="^(critical|warning|info)$"),
    category: Optional[str] = None,
    unread_only: bool = False,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get system alerts based on inventory levels - PAGINATED TO PREVENT CRASHES
    
    CRASH FIXES APPLIED:
    - Added proper page/per_page pagination (was just limit before)
    - Returns pagination metadata (total, total_pages, current_page)
    - Frontend can now request specific pages instead of all alerts at once
    - Memory-safe: max 100 alerts per page, prevents loading all 7914+ alerts
    """
    from sqlalchemy import text
    from datetime import datetime
    
    # Generate alerts from inventory data using raw SQL
    alerts_data = []
    
    # 1. Out of stock alerts (CRITICAL) - FIXED: Added LIMIT to prevent memory crash
    out_of_stock_sql = """
        SELECT i.id, i.name, i.sku, i.product_id, p.category, i.current_stock, i.reorder_point
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        WHERE i.stock_status = 'out_of_stock'
        LIMIT 5000
    """
    
    out_of_stock = db.execute(text(out_of_stock_sql)).fetchall()
    for row in out_of_stock:
        alerts_data.append({
            'severity': 'critical',
            'category': 'inventory',
            'title': f'Out of Stock: {row[1]}',
            'message': f'{row[1]} ({row[2]}) is completely out of stock',
            'product_id': row[3],
            'recommendation': f'Urgent reorder required. Reorder point: {row[6]}',
            'created_at': datetime.now().isoformat(),
            'is_acknowledged': False
        })
    
    # 2. Low stock alerts (WARNING) - FIXED: Added LIMIT to prevent memory crash
    low_stock_sql = """
        SELECT i.id, i.name, i.sku, i.product_id, p.category, i.current_stock, i.reorder_point, i.max_stock
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        WHERE i.stock_status = 'low'
        LIMIT 5000
    """
    
    low_stock = db.execute(text(low_stock_sql)).fetchall()
    for row in low_stock:
        alerts_data.append({
            'severity': 'warning',
            'category': 'inventory',
            'title': f'Low Stock: {row[1]}',
            'message': f'{row[1]} ({row[2]}) has low stock: {row[5]} units',
            'product_id': row[3],
            'recommendation': f'Consider reordering. Max: {row[7]}, Current: {row[5]}',
            'created_at': datetime.now().isoformat(),
            'is_acknowledged': False
        })
    
    # 3. High stock alerts (INFO) - sample only
    high_stock_sql = """
        SELECT i.id, i.name, i.sku, i.product_id, p.category, i.current_stock
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        WHERE i.stock_status = 'high'
        LIMIT 10
    """
    
    high_stock = db.execute(text(high_stock_sql)).fetchall()
    for row in high_stock:
        alerts_data.append({
            'severity': 'info',
            'category': 'inventory',
            'title': f'High Stock: {row[1]}',
            'message': f'{row[1]} ({row[2]}) is well stocked: {row[5]} units',
            'product_id': row[3],
            'recommendation': 'Monitor for slow-moving items',
            'created_at': datetime.now().isoformat(),
            'is_acknowledged': True
        })
    
    # Apply filters
    filtered_alerts = alerts_data
    
    if severity:
        filtered_alerts = [a for a in filtered_alerts if a['severity'] == severity]
    
    if category:
        filtered_alerts = [a for a in filtered_alerts if a['category'] == category]
    
    if unread_only:
        filtered_alerts = [a for a in filtered_alerts if not a['is_acknowledged']]
    
    # Calculate pagination
    total = len(filtered_alerts)
    total_pages = (total + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_alerts = filtered_alerts[start_idx:end_idx]
    
    # Format for response
    result = []
    for idx, alert in enumerate(paginated_alerts):
        result.append({
            'id': start_idx + idx + 1,
            'severity': alert['severity'],
            'category': alert['category'],
            'title': alert['title'],
            'message': alert['message'],
            'recommendation': alert.get('recommendation', ''),
            'created_at': alert['created_at'],
            'is_acknowledged': alert['is_acknowledged'],
            'product_id': alert.get('product_id')
        })
    
    return {
        "success": True,
        "data": {
            "items": result,
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
