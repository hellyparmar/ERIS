"""
Enterprise Retail Intelligence System v3.0
DASHBOARD API - Real-Time Metrics with Actual Data

Provides time-aware, realistic metrics using actual database queries.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, select
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any

# Database Imports
from app.api.db import get_db
from app.api.db.models import Sale, SaleItem
from app.models.multitenant_models import Product, Inventory, Customer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

def get_latest_data_date(db: Session) -> datetime:
    """Get the date of the most recent sale, or now if no sales"""
    last_date = db.query(func.max(Sale.transaction_date)).scalar()
    return last_date if last_date else datetime.now()

@router.get("/realtime")
async def get_realtime_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get real-time dashboard metrics from the database
    """
    try:
        # 1. Determine "Today" (use latest data date to ensure demo data shows up)
        latest_date = get_latest_data_date(db)
        start_of_day = latest_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = latest_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # 2. Key Metrics
        # Total Revenue (All time)
        total_revenue = db.query(func.sum(Sale.total_amount)).scalar() or 0.0
        
        # Total Orders (All time)
        total_orders = db.query(func.count(Sale.id)).scalar() or 0
        
        # Average Order Value (All time)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0.0
        
        # "Today's" Revenue (Latest active day)
        today_revenue = db.query(func.sum(Sale.total_amount))\
            .filter(Sale.transaction_date >= start_of_day)\
            .filter(Sale.transaction_date <= end_of_day)\
            .scalar() or 0.0
            
        # "Active Orders" (Simulate based on today's count)
        today_orders = db.query(func.count(Sale.id))\
            .filter(Sale.transaction_date >= start_of_day)\
            .filter(Sale.transaction_date <= end_of_day)\
            .scalar() or 0
            
        active_orders = int(today_orders * 0.1) # Simulate current active processing
        
        # 3. Top Products (by Revenue)
        top_products = get_top_products(db, limit=5)
        
        # 4. Low Stock Alerts
        low_stock_items = get_low_stock_items(db, limit=10)
        
        # 5. Revenue Trend (Last 7 days relative to latest data)
        revenue_trend = get_revenue_trend(db, latest_date, days=7)
        
        # Calculate time multiplier for UI "aliveness" feel
        current_hour = datetime.now().hour
        time_multiplier = get_time_multiplier(current_hour)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "data_date": latest_date.isoformat(), # For debug/UI info
            "today_revenue": round(float(today_revenue), 2),
            "total_revenue": round(float(total_revenue), 2),
            "active_orders": active_orders,
            "total_orders": total_orders,
            "avg_order_value": round(float(avg_order_value), 2),
            "top_products": top_products,
            "low_stock_alerts": low_stock_items,
            "revenue_trend": revenue_trend,
            "time_multiplier": round(time_multiplier, 2)
        }
        
    except Exception as e:
        logger.error(f"Error fetching realtime metrics: {e}")
        # Fallback to empty structure with error indication if critical failure
        # But try to avoid fallback to prevent confusion with mock data
        raise HTTPException(status_code=500, detail=str(e))


def get_top_products(db: Session, limit: int = 5) -> List[Dict]:
    """Get top selling products by revenue"""
    results = db.query(
        Product.name,
        Product.category,
        func.sum(SaleItem.quantity).label("units"),
        func.sum(SaleItem.total_price).label("revenue")
    ).join(SaleItem, Product.id == SaleItem.product_id)\
     .group_by(Product.id)\
     .order_by(desc("revenue"))\
     .limit(limit)\
     .all()
    
    top_products = []
    for rank, (name, category, units, revenue) in enumerate(results, 1):
        top_products.append({
            "rank": rank,
            "name": name,
            "category": category,
            "units_sold": int(units),
            "revenue": round(float(revenue), 2),
            "growth": 0 # Placeholder for complex growth calc
        })
    
    return top_products

def get_low_stock_items(db: Session, limit: int = 10) -> List[Dict]:
    """Get items with stock below 20"""
    results = db.query(Product, Inventory)\
        .join(Inventory, Product.id == Inventory.product_id)\
        .filter(Inventory.stock_quantity < 20)\
        .order_by(Inventory.stock_quantity.asc())\
        .limit(limit)\
        .all()
        
    alerts = []
    for product, inventory in results:
        alerts.append({
            "product_id": product.id,
            "product_name": product.name,
            "current_stock": int(inventory.stock_quantity),
            "reorder_point": 20, # Static for now
            "severity": "critical" if inventory.stock_quantity < 5 else "warning"
        })
    return alerts

def get_revenue_trend(db: Session, end_date: datetime, days: int = 7) -> List[Dict]:
    """Get revenue per day for the last N days ending at end_date"""
    start_date = end_date - timedelta(days=days-1)
    
    # Date handling is delegated to SQLAlchemy and the PostgreSQL dialect.
    # Grouping by date is handled using the database's native date functions.
    
    results = db.query(
        func.date(Sale.transaction_date).label("date"),
        func.sum(Sale.total_amount).label("revenue")
    ).filter(Sale.transaction_date >= start_of_day(start_date))\
     .filter(Sale.transaction_date <= end_of_day(end_date))\
     .group_by("date")\
     .order_by("date")\
     .all()
     
    trend = []
    # Fill gaps? For now just return what we have
    for date_str, revenue in results:
        trend.append({
            "date": date_str,
            "revenue": round(float(revenue), 2)
        })
    return trend

def start_of_day(dt: datetime):
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)

def end_of_day(dt: datetime):
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

def get_time_multiplier(hour: int) -> float:
    """Calculate time-of-day multiplier"""
    if 6 <= hour < 12:
        return 0.6 + (hour - 6) * 0.033
    elif 12 <= hour < 18:
        return 1.0 + (hour - 12) * 0.033
    elif 18 <= hour < 23:
        return 1.0 - (hour - 18) * 0.04
    else:
        return 0.4

@router.get("/summary")
async def get_dashboard_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get high-level dashboard summary"""
    try:
        total_products = db.query(func.count(Product.id)).scalar()
        total_customers = db.query(func.count(Customer.id)).scalar()
        total_orders = db.query(func.count(Sale.id)).scalar()
        dead_stock = db.query(func.count(Product.id)).filter(Product.is_dead_stock == True).scalar()
        credit_customers = db.query(func.count(Customer.id)).filter(Customer.credit_enabled == True).scalar()
        
        # Determine latest date for context
        latest_date = get_latest_data_date(db)
        
        return {
            "total_products": total_products,
            "total_customers": total_customers,
            "total_orders": total_orders,
            "dead_stock_count": dead_stock,
            "customers_with_credit": credit_customers,
            "data_currency_date": latest_date.isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return {"error": str(e)}
