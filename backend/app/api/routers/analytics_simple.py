"""
Simple Analytics Router
Keep only: Total sales, top products, basic charts
Remove: Cohort analysis, RFM, causal inference, complex forecasting
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.db import get_db
from app.api.db.models import Sale, SaleItem, Product
from datetime import datetime, timedelta
from typing import Dict, Any, List

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/summary")
def get_summary(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get basic sales summary for the dashboard.
    
    Returns:
    {
        'total_sales': 150000,
        'orders': 250,
        'avg_order_value': 600,
        'top_products': [
            {'product_id': 5, 'name': 'Widget A', 'quantity': 500, 'revenue': 50000}
        ]
    }
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total sales
        total_sales_query = db.query(
            func.sum(Sale.total_amount).label('total')
        ).filter(Sale.created_at >= cutoff_date).first()
        
        total_sales = float(total_sales_query.total or 0)
        
        # Order count
        order_count_query = db.query(
            func.count(Sale.id).label('count')
        ).filter(Sale.created_at >= cutoff_date).first()
        
        order_count = order_count_query.count or 0
        
        # Average order value
        avg_order = total_sales / order_count if order_count > 0 else 0
        
        # Top products
        top_products = db.query(
            Product.id,
            Product.name,
            func.sum(SaleItem.quantity).label('qty'),
            func.sum(SaleItem.unit_price * SaleItem.quantity).label('revenue')
        ).join(SaleItem).join(Sale).filter(
            Sale.created_at >= cutoff_date
        ).group_by(Product.id, Product.name).order_by(
            func.sum(SaleItem.unit_price * SaleItem.quantity).desc()
        ).limit(10).all()
        
        top_products_list = [
            {
                'product_id': p.id,
                'name': p.name,
                'quantity': int(p.qty or 0),
                'revenue': float(p.revenue or 0)
            }
            for p in top_products
        ]
        
        return {
            'total_sales': round(total_sales, 2),
            'orders': order_count,
            'avg_order_value': round(avg_order, 2),
            'period_days': days,
            'top_products': top_products_list,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sales-trend")
def get_sales_trend(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Daily sales trend for the last N days.
    
    Returns:
    {
        'dates': ['2026-02-01', '2026-02-02', ...],
        'sales': [10000, 12000, 11000, ...],
        'avg_daily': 11000
    }
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        daily_sales = db.query(
            func.date(Sale.created_at).label('date'),
            func.sum(Sale.total_amount).label('daily_total')
        ).filter(
            Sale.created_at >= cutoff_date
        ).group_by(
            func.date(Sale.created_at)
        ).order_by(
            func.date(Sale.created_at)
        ).all()
        
        dates = [sale.date.strftime('%Y-%m-%d') for sale in daily_sales]
        sales = [float(sale.daily_total or 0) for sale in daily_sales]
        
        avg_daily = sum(sales) / len(sales) if sales else 0
        
        return {
            'dates': dates,
            'sales': sales,
            'avg_daily': round(avg_daily, 2),
            'period_days': days,
            'data_points': len(dates)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hourly-breakdown")
def get_hourly_breakdown(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Sales breakdown by hour of day (useful for staffing).
    
    Returns:
    {
        'hours': [9, 10, 11, ..., 21],
        'sales': [1000, 1500, 2000, ..., 500]
    }
    """
    try:
        # Sales by hour of day
        hourly_data = db.query(
            func.extract('hour', Sale.created_at).label('hour'),
            func.sum(Sale.total_amount).label('total')
        ).group_by(
            func.extract('hour', Sale.created_at)
        ).order_by(
            func.extract('hour', Sale.created_at)
        ).all()
        
        hours = []
        sales = []
        for hour, total in hourly_data:
            hours.append(int(hour) if hour is not None else 0)
            sales.append(float(total or 0))
        
        return {
            'hours': hours,
            'sales': sales,
            'peak_hour': hours[sales.index(max(sales))] if sales else None,
            'peak_sales': max(sales) if sales else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory-status")
def get_inventory_status(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Current inventory status.
    
    Returns:
    {
        'total_items': 5000,
        'total_value': 250000,
        'low_stock_items': 3,
        'out_of_stock_items': 1
    }
    """
    try:
        from app.api.db.models import Inventory
        
        # Total items and value
        inventory_summary = db.query(
            func.sum(Inventory.quantity).label('total_qty'),
            func.sum(Inventory.quantity * Inventory.unit_cost).label('total_value'),
            func.count(Inventory.id).label('product_count')
        ).first()
        
        # Low stock (less than 10 units)
        low_stock = db.query(func.count(Inventory.id)).filter(
            Inventory.quantity < 10,
            Inventory.quantity > 0
        ).scalar() or 0
        
        # Out of stock
        out_of_stock = db.query(func.count(Inventory.id)).filter(
            Inventory.quantity <= 0
        ).scalar() or 0
        
        return {
            'total_items': int(inventory_summary.total_qty or 0),
            'total_value': float(inventory_summary.total_value or 0),
            'products': int(inventory_summary.product_count or 0),
            'low_stock_count': int(low_stock),
            'out_of_stock_count': int(out_of_stock),
            'health': 'good' if out_of_stock == 0 else 'warning' if out_of_stock < 3 else 'critical'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
