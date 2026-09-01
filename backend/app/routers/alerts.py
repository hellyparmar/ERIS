from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, select
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models import Alert, Inventory, Product, AlertSeverity
from app.models.users import User
from app.api.deps import get_current_active_user, get_outlet_scope
from app.core.data_isolation import require_outlet_access

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/list")
async def get_alerts(
    severity: Optional[str] = Query(None, pattern="^(critical|warning|info)$"),
    category: Optional[str] = None,
    unread_only: bool = False,
    outlet_id: Optional[int] = Query(None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get system alerts based on inventory levels with outlet scoping"""
    from sqlalchemy import text
    from datetime import datetime
    
    allowed_outlets = get_outlet_scope(current_user, db)
    outlet_clause = ""
    params = {}
    if allowed_outlets:
        if outlet_id:
            if not require_outlet_access(current_user, outlet_id):
                raise HTTPException(status_code=403, detail="Access denied to this outlet")
            outlet_clause = " AND i.outlet_id = :outlet_id "
            params["outlet_id"] = outlet_id
        else:
            outlet_clause = f" AND i.outlet_id IN ({','.join(str(oid) for oid in allowed_outlets)}) "
    elif outlet_id:
        outlet_clause = " AND i.outlet_id = :outlet_id "
        params["outlet_id"] = outlet_id
    
    # Generate alerts from inventory data using raw SQL
    alerts_data = []
    
    # 1. Out of stock alerts (CRITICAL)
    out_of_stock_sql = f"""
        SELECT i.id, i.name, i.sku, i.product_id, p.category, i.current_stock, i.reorder_point
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        WHERE i.stock_status = 'out_of_stock' {outlet_clause}
        LIMIT 5000
    """
    
    out_of_stock = db.execute(text(out_of_stock_sql), params).fetchall()
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
    
    # 2. Low stock alerts (WARNING)
    low_stock_sql = f"""
        SELECT i.id, i.name, i.sku, i.product_id, p.category, i.current_stock, i.reorder_point, i.max_stock
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        WHERE i.stock_status = 'low' {outlet_clause}
        LIMIT 5000
    """
    
    low_stock = db.execute(text(low_stock_sql), params).fetchall()
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
    high_stock_sql = f"""
        SELECT i.id, i.name, i.sku, i.product_id, p.category, i.current_stock
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        WHERE i.stock_status = 'high' {outlet_clause}
        LIMIT 10
    """
    
    high_stock = db.execute(text(high_stock_sql), params).fetchall()
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
        result = await db.execute(select(Alert).where(and_(
                Alert.related_product_id == product.id,
                Alert.category == "stock",
                Alert.is_acknowledged == False
            )))
        existing = result.scalar_one_or_none()
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
        result = await db.execute(select(Alert).where(and_(
                Alert.related_product_id == product.id,
                Alert.category == "stock",
                Alert.severity == AlertSeverity.CRITICAL,
                Alert.is_acknowledged == False
            )))
        existing = result.scalar_one_or_none()
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
