"""
Enterprise Retail Intelligence System v3.0
ANALYTICS ROUTER

Endpoints for dashboard metrics, alerts, and chart data.
"""

from fastapi import APIRouter, Query, HTTPException
from app.api.schemas import MetricsResponse, AlertsResponse, ChartDataResponse, Alert, ChartDataPoint
from app.api.services.data_service import DataService
import app.api.mock_data as mock_data

router = APIRouter()
data_service = DataService()

@router.get("/analytics/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get dashboard KPI metrics.
    
    Returns totalRevenue, avgDailySales, inventoryValue, stockoutRisk, etc.
    """
    try:
        # Generate sample data (in production, this would query database)
        demand_data = mock_data.generate_demand_data(90)
        inventory_data = mock_data.generate_inventory_data(20)
        metrics = mock_data.calculate_metrics(demand_data, inventory_data)
        
        # Add alert counts
        alerts = mock_data.generate_alerts(inventory_data, demand_data)
        metrics['alertCount'] = len(alerts)
        metrics['criticalAlertCount'] = len([a for a in alerts if a['severity'] == 'critical'])
        
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/alerts", response_model=AlertsResponse)
async def get_alerts(
    severity: str = Query("all", enum=["all", "critical", "warning", "info"])
):
    """
    Get inventory alerts filtered by severity.
    
    Query params:
    - severity: "all", "critical", "warning", or "info"
    """
    try:
        # Generate data
        demand_data = mock_data.generate_demand_data(90)
        inventory_data = mock_data.generate_inventory_data(20)
        all_alerts = mock_data.generate_alerts(inventory_data, demand_data)
        
        # Filter by severity
        if severity != "all":
            filtered_alerts = [a for a in all_alerts if a['severity'] == severity]
        else:
            filtered_alerts = all_alerts
        
        return {
            "alerts": filtered_alerts,
            "total": len(filtered_alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/chart-data", response_model=ChartDataResponse)
async def get_chart_data(
    days: int = Query(30, ge=1, le=365),
    forecast_days: int = Query(15, ge=1, le=90)
):
    """
    Get sales chart data (historical + forecast).
    
    Query params:
    - days: Number of historical days (default: 30)
    - forecast_days: Number of forecast days (default: 15)
    """
    try:
        # Generate historical data
        demand_data = mock_data.generate_demand_data(days)
        forecast_data = mock_data.generate_forecast_data(demand_data, forecast_days)
        
        # Format for chart
        historical = [
            {
                "date": d['date'],
                "actual": d['sales'],
                "predicted": None,
                "lowerBound": None,
                "upperBound": None
            }
            for d in demand_data
        ]
        
        forecast = [
            {
                "date": f['date'],
                "actual": None,
                "predicted": f['predicted'],
                "lowerBound": f['lowerBound'],
                "upperBound": f['upperBound']
            }
            for f in forecast_data
        ]
        
        return {
            "data": historical + forecast,
            "metadata": {
                "historical_days": days,
                "forecast_days": forecast_days
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
