"""
Enterprise Retail Intelligence System v3.0
ANALYTICS ROUTER
Endpoints for dashboard metrics, alerts, and chart data.
"""

from fastapi import APIRouter, Query, HTTPException, Depends, Request
from typing import List, Optional
from pydantic import BaseModel
import random
from datetime import datetime, timedelta
from app.middleware.auth import get_current_user
from app.middleware.rate_limiter import limiter
from app.models.multitenant_models import User, Product, Inventory
from app.models.sale import Sale, SaleItem
from app.models.schema import Alert
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from app.schemas.analytics import MetricData, AlertsResponse, ChartDataResponse
from datetime import timezone

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

@router.get("/metrics", response_model=MetricData)
@limiter.limit("20/minute")
async def get_metrics(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get high-level dashboard KPI metrics.
    
    This includes total organization revenue, average daily sales, 
    inventory value, stockout risk counts, and unacknowledged alerts.
    """
    # 1. Total Revenue (Organization wide)
    total_revenue = db.query(func.sum(Sale.total_amount)).join(
        SaleItem
    ).join(
        Product, SaleItem.product_id == Product.id
    ).filter(Product.organization_id == current_user.organization_id).scalar() or 0.0
    
    # 2. Avg Daily Sales (last 30 days)
    thirty_days_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
    avg_daily = db.query(func.avg(Sale.total_amount)).filter(
        Sale.transaction_date >= thirty_days_ago
    ).scalar() or 0.0
    
    # 3. Inventory Value
    inventory_value = db.query(func.sum(Product.cost_price * Inventory.current_stock)).join(
        Inventory, Product.id == Inventory.product_id
    ).filter(Product.organization_id == current_user.organization_id).scalar() or 0.0
    
    # 4. Stockout Risk
    stockout_risk_count = db.query(func.count(Inventory.id)).join(Product).filter(
        Product.organization_id == current_user.organization_id,
        Inventory.current_stock <= Inventory.reorder_point
    ).scalar() or 0
    
    # 5. Alert count
    alert_count = db.query(func.count(Alert.id)).join(Product).filter(
        Product.organization_id == current_user.organization_id,
        Alert.is_acknowledged == False
    ).scalar() or 0
    
    critical_alerts = db.query(func.count(Alert.id)).join(Product).filter(
        Product.organization_id == current_user.organization_id,
        Alert.severity == "critical",
        Alert.is_acknowledged == False
    ).scalar() or 0
    
    return {
        "totalRevenue": float(total_revenue),
        "avgDailySales": float(avg_daily),
        "inventoryValue": float(inventory_value),
        "stockoutRisk": float(stockout_risk_count),
        "alertCount": alert_count,
        "criticalAlertCount": critical_alerts
    }

@router.get("/alerts", response_model=AlertsResponse)
@limiter.limit("20/minute")
async def get_alerts(
    request: Request,
    severity: str = Query("all", enum=["all", "critical", "warning", "info"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get unacknowledged inventory alerts for the organization.
    
    Filter by severity: all, critical, warning, or info.
    """
    query = db.query(Alert).join(Product).filter(
        Product.organization_id == current_user.organization_id,
        Alert.is_acknowledged == False
    )
    
    if severity != "all":
        query = query.filter(Alert.severity == severity)
        
    alerts = query.order_by(Alert.created_at.desc()).limit(50).all()
    
    return {
        "alerts": [
            {
                "id": a.id, 
                "severity": a.severity.value if hasattr(a.severity, 'value') else a.severity, 
                "message": a.message, 
                "timestamp": str(a.created_at)
            } 
            for a in alerts
        ], 
        "total": len(alerts)
    }

@router.get("/chart-data", response_model=ChartDataResponse)
@limiter.limit("20/minute")
async def get_chart_data(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    forecast_days: int = Query(15, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get sales chart data including historical trends and AI-powered forecasts.
    """
    # 1. Historical Data from DB
    start_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    
    historical_sales = db.query(
        func.date(Sale.transaction_date).label('date'),
        func.sum(Sale.total_amount).label('total')
    ).join(Product).filter(
        Product.organization_id == current_user.organization_id,
        Sale.transaction_date >= start_date
    ).group_by(func.date(Sale.transaction_date)).all()
    
    sales_map = {str(row.date): float(row.total) for row in historical_sales}
    
    data = []
    for i in range(days):
        date_str = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        data.append({
            "date": date_str,
            "actual": sales_map.get(date_str, 0.0),
            "predicted": None,
            "lowerBound": None,
            "upperBound": None
        })
    
    # 2. Mock Forecast (placeholder for Phase 5 integration)
    last_date = start_date + timedelta(days=days-1)
    for i in range(1, forecast_days + 1):
        date_str = (last_date + timedelta(days=i)).strftime("%Y-%m-%d")
        pred = 55000 + random.randint(-2000, 2000)
        data.append({
            "date": date_str,
            "actual": None,
            "predicted": pred,
            "lowerBound": pred - 5000,
            "upperBound": pred + 5000
        })
            
    return {
        "data": data,
        "metadata": {
            "historical_days": days,
            "forecast_days": forecast_days,
            "organization_id": str(current_user.organization_id)
        }
    }
