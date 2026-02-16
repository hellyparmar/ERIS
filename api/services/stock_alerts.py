"""
Stock Alerts Service
Real-time low stock monitoring with severity levels
Per CLAUDE.md Part 3.2
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from api.db.models import Alert, Inventory, Product

# Alert severity thresholds
SEVERITY_CRITICAL = 'critical'  # Stock = 0
SEVERITY_WARNING = 'warning'    # Stock <= reorder_point
SEVERITY_INFO = 'info'          # Stock <= reorder_point * 1.5

def check_stock_levels(db: Session) -> List[Dict]:
    """
    Check all inventory for low stock conditions
    Generate alerts for items below thresholds
    
    Returns:
        List of generated alerts
    """
    alerts_generated = []
    
    # Get all inventory with products
    inventory_items = db.query(Inventory, Product).join(
        Product, Inventory.product_id == Product.id
    ).all()
    
    for inv, product in inventory_items:
        severity = None
        message = None
        
        # Determine severity
        if inv.current_stock == 0:
            severity = SEVERITY_CRITICAL
            message = f"{product.name}: OUT OF STOCK - Reorder immediately"
        elif inv.current_stock <= inv.reorder_point:
            severity = SEVERITY_WARNING
            message = f"{product.name}: Stock {inv.current_stock} units - Reorder point is {inv.reorder_point}"
        elif inv.current_stock <= (inv.reorder_point * 1.5):
            severity = SEVERITY_INFO
            message = f"{product.name}: Stock {inv.current_stock} units - Approaching reorder point ({inv.reorder_point})"
        
        if severity:
            # Check if alert already exists
            existing = db.query(Alert).filter(
                and_(
                    Alert.product_id == product.id,
                    Alert.alert_type == 'reorder',
                    Alert.status == 'active',
                    Alert.severity == severity
                )
            ).first()
            
            if not existing:
                # Create new alert
                alert = Alert(
                    product_id=product.id,
                    alert_type='reorder',
                    severity=severity,
                    message=message,
                    status='active',
                    created_at=datetime.now()
                )
                db.add(alert)
                alerts_generated.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'severity': severity,
                    'current_stock': inv.current_stock,
                    'reorder_point': inv.reorder_point
                })
    
    db.commit()
    return alerts_generated

def get_active_alerts(
    db: Session,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> Dict:
    """
    Get active stock alerts with filtering and pagination
    
    Args:
        db: Database session
        severity: Filter by severity (critical/warning/info)
        category: Filter by product category
        limit: Results per page
        offset: Pagination offset
    
    Returns:
        {
            'alerts': [...],
            'total': int,
            'critical_count': int,
            'warning_count': int,
            'info_count': int
        }
    """
    # Build query
    query = db.query(Alert, Product).join(
        Product, Alert.product_id == Product.id
    ).filter(
        and_(
            Alert.alert_type == 'reorder',
            Alert.status == 'active'
        )
    )
    
    # Apply filters
    if severity:
        query = query.filter(Alert.severity == severity)
    if category:
        query = query.filter(Product.category == category)
    
    # Get counts by severity
    critical_count = db.query(Alert).filter(
        and_(
            Alert.alert_type == 'reorder',
            Alert.status == 'active',
            Alert.severity == SEVERITY_CRITICAL
        )
    ).count()
    
    warning_count = db.query(Alert).filter(
        and_(
            Alert.alert_type == 'reorder',
            Alert.status == 'active',
            Alert.severity == SEVERITY_WARNING
        )
    ).count()
    
    info_count = db.query(Alert).filter(
        and_(
            Alert.alert_type == 'reorder',
            Alert.status == 'active',
            Alert.severity == SEVERITY_INFO
        )
    ).count()
    
    # Get total and paginated results
    total = query.count()
    results = query.order_by(
        Alert.created_at.desc()
    ).limit(limit).offset(offset).all()
    
    # Format alerts
    alerts = []
    for alert, product in results:
        # Get inventory
        inv = db.query(Inventory).filter(
            Inventory.product_id == product.id
        ).first()
        
        alerts.append({
            'id': alert.id,
            'product_id': product.id,
            'product_name': product.name,
            'category': product.category,
            'severity': alert.severity,
            'message': alert.message,
            'current_stock': inv.current_stock if inv else 0,
            'reorder_point': inv.reorder_point if inv else 0,
            'created_at': alert.created_at.isoformat() if alert.created_at else None,
            'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
        })
    
    return {
        'alerts': alerts,
        'total': total,
        'critical_count': critical_count,
        'warning_count': warning_count,
        'info_count': info_count
    }

def acknowledge_alert(alert_id: int, user_id: int, db: Session) -> Dict:
    """
    Mark alert as acknowledged
    
    Args:
        alert_id: Alert ID
        user_id: User who acknowledged
        db: Database session
    
    Returns:
        {'success': bool, 'error': str or None}
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        return {
            'success': False,
            'error': f'Alert {alert_id} not found'
        }
    
    alert.acknowledged_at = datetime.now()
    alert.acknowledged_by = user_id
    alert.status = 'acknowledged'
    
    db.commit()
    
    return {
        'success': True,
        'error': None
    }
