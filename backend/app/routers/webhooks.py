"""
R-DIOS Webhook endpoints for n8n to trigger.
These are internal endpoints called by n8n workflows.
"""
from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, timedelta
import os

from app.database import get_db
from app.models.schema import InventoryMovement, Product, Outlet, Alert, Sale

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

N8N_SECRET = os.getenv("N8N_WEBHOOK_SECRET", "rdios-n8n-secret")


def verify_n8n_secret(x_n8n_secret: Optional[str] = Header(None)):
    """Verify n8n webhook secret from header."""
    if x_n8n_secret != N8N_SECRET:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")


@router.post("/check-low-stock")
def webhook_check_low_stock(
    db: Session = Depends(get_db),
    _: None = Depends(verify_n8n_secret),
):
    """
    n8n calls this daily to check for low stock.
    Returns list of critical stock situations for n8n to send alerts.
    """
    # Query for low stock items
    low_stock = (
        db.query(
            InventoryMovement,
            Product.name,
            Product.category,
            Outlet.name.label("oname")
        )
        .join(Product, Product.id == InventoryMovement.product_id)
        .join(Outlet, Outlet.id == InventoryMovement.outlet_id)
        .filter(InventoryMovement.quantity_on_hand <= InventoryMovement.reorder_level)
        .filter(Product.is_active == True)
        .limit(50)
        .all()
    )

    alerts_created = 0
    items = []
    
    for inv, pname, pcat, oname in low_stock:
        severity = "critical" if inv.quantity_on_hand == 0 else "warning"
        title = f"{'Out of stock' if inv.quantity_on_hand == 0 else 'Low stock'}: {pname}"
        
        # Check if alert already exists
        existing = db.query(Alert).filter(
            Alert.title == title,
            Alert.outlet_id == inv.outlet_id,
            Alert.is_resolved == False
        ).first()
        
        if not existing:
            db.add(Alert(
                outlet_id=inv.outlet_id,
                product_id=inv.product_id,
                severity=severity,
                category="inventory",
                title=title,
                message=f"{pname} ({pcat}) has {inv.quantity_on_hand} units at {oname} (reorder: {inv.reorder_level}).",
                is_read=False,
                is_resolved=False
            ))
            alerts_created += 1
        
        items.append({
            "product": pname,
            "outlet": oname,
            "stock": inv.quantity_on_hand,
            "reorder_level": inv.reorder_level,
            "severity": severity
        })

    db.commit()
    return {
        "alerts_created": alerts_created,
        "total_low_stock": len(items),
        "items": items
    }


@router.get("/daily-summary")
def webhook_daily_summary(
    db: Session = Depends(get_db),
    _: None = Depends(verify_n8n_secret),
):
    """n8n calls this for daily email reports."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Get yesterday's revenue
    yesterday_rev = (
        db.query(func.sum(Sale.total_amount))
        .filter(Sale.sale_date == yesterday)
        .scalar() or 0
    )
    
    # Get yesterday's order count
    yesterday_orders = (
        db.query(func.count(Sale.id))
        .filter(Sale.sale_date == yesterday)
        .scalar() or 0
    )
    
    # Get unread alerts
    unread_alerts = (
        db.query(func.count(Alert.id))
        .filter(Alert.is_read == False, Alert.is_resolved == False)
        .scalar() or 0
    )
    
    return {
        "date": str(yesterday),
        "revenue": round(yesterday_rev, 2),
        "orders": yesterday_orders,
        "unread_alerts": unread_alerts,
        "report_url": "http://localhost:5173/dashboard",
    }
