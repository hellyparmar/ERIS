"""
Enterprise Retail Intelligence System v3.0
ANALYTICS ROUTER

Endpoints for dashboard metrics, alerts, chart data, and model performance.
"""

import logging
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.schemas import MetricsResponse, AlertsResponse, ChartDataResponse, Alert, ChartDataPoint
from app.api.services.data_service import DataService
from app.database import get_db
from app.core.security import get_current_user
from app.services.model_tracker import ModelTracker
import app.api.mock_data as mock_data

logger = logging.getLogger(__name__)

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

@router.get("/dashboard/realtime")
async def get_dashboard_realtime():
    """
    Get real-time dashboard metrics for the frontend.
    
    Returns: total_orders, total_revenue, today_revenue, active_orders, 
             avg_order_value, time_multiplier, data_source, recent_transactions
    """
    try:
        demand_data = mock_data.generate_demand_data(30)
        
        total_orders = len(demand_data)
        total_revenue = sum(d['revenue'] for d in demand_data)
        today_revenue = sum(d['revenue'] for d in demand_data[-1:])
        active_orders = max(1, int(total_orders * 0.15))
        avg_order_value = int(total_revenue / total_orders) if total_orders > 0 else 0
        time_multiplier = 1.0 + (0.3 * (len([d for d in demand_data[-7:] if d['revenue'] > total_revenue/30])) / 7)
        
        # Generate recent transactions for display
        recent_transactions = [
            {
                "id": f"TXN-{i:06d}",
                "customer": f"Customer-{i}",
                "amount": int(demand_data[i % len(demand_data)]['revenue'] / 5),
                "status": "completed",
                "timestamp": f"2026-04-{max(1, min(2, (i % 30) + 1)):02d}"
            }
            for i in range(min(10, len(demand_data)))
        ]
        
        return {
            "total_orders": total_orders,
            "total_revenue": int(total_revenue),
            "today_revenue": int(today_revenue),
            "active_orders": active_orders,
            "avg_order_value": avg_order_value,
            "time_multiplier": time_multiplier,
            "data_source": "mock",
            "recent_transactions": recent_transactions
        }
    except Exception as e:
        # Return fallback data if error occurs
        return {
            "total_orders": 0,
            "total_revenue": 0,
            "today_revenue": 0,
            "active_orders": 0,
            "avg_order_value": 0,
            "time_multiplier": 1.0,
            "data_source": "error",
            "recent_transactions": []
        }


# ============================================================
# MODEL PERFORMANCE ENDPOINTS
# ============================================================

@router.get("/model-performance")
async def get_model_performance(
    outlet_id: str = Query(..., description="Outlet ID"),
    days: int = Query(30, ge=7, le=90, description="Days to evaluate (7-90)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get model performance metrics for forecasting model evaluation.
    
    Essential for MSc Data Science project demonstrating model evaluation discipline.
    
    Compares forecasts made N days ago against actual values to compute:
    - MAE (Mean Absolute Error)
    - MAPE (Mean Absolute Percentage Error)
    - RMSE (Root Mean Square Error)
    - Directional Accuracy (% correct up/down predictions)
    - Bias (systematic over/under-prediction)
    - Performance trends over time
    - Worst predictions for debugging
    
    Query Parameters:
    - outlet_id: Target outlet for evaluation
    - days: Evaluation period in days (default 30, range 7-90)
    
    Returns complete model performance report with metrics, trends, and worst cases.
    """
    try:
        tracker = ModelTracker(db)
        
        # Get overall performance evaluation
        evaluation = tracker.evaluate_past_forecasts(outlet_id, days_back=days)
        
        if evaluation.get('status') != 'success':
            return {
                'status': evaluation.get('status', 'error'),
                'message': evaluation.get('message', 'Could not evaluate model performance'),
                'outlet_id': outlet_id,
                'evaluation_period': evaluation.get('evaluation_period'),
                'data_available': False,
            }
        
        # Get retraining recommendation
        retrain_assessment = tracker.should_retrain(outlet_id, mape_threshold=15.0, days_window=7)
        
        return {
            'status': 'success',
            'outlet_id': outlet_id,
            'model_name': evaluation.get('model_name', 'Unknown'),
            'evaluation_period': evaluation.get('evaluation_period'),
            'sample_size': evaluation.get('sample_size'),
            'data_available': True,
            
            # Core metrics
            'metrics': evaluation.get('metrics', {}),
            
            # Performance trend (useful for charting)
            'performance_trend': evaluation.get('performance_trend', []),
            
            # Worst predictions (for debugging)
            'worst_predictions': evaluation.get('worst_predictions', []),
            
            # Retraining recommendation
            'retraining': {
                'should_retrain': retrain_assessment.get('should_retrain', False),
                'reason': retrain_assessment.get('reason', ''),
                'current_mape': retrain_assessment.get('current_mape'),
                'threshold': retrain_assessment.get('threshold'),
            },
        }
        
    except Exception as e:
        logger.error(f"Model performance analysis error: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'message': f'Model performance analysis failed: {str(e)}',
            'outlet_id': outlet_id,
            'data_available': False,
        }
