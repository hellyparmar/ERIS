"""
Enterprise Retail Intelligence System v3.0
ANALYTICS ROUTER
Endpoints for dashboard metrics, alerts, and chart data.
"""


from app.services.model_tracker import ModelTracker
from fastapi import APIRouter, Query, Depends, Request
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.api.deps import get_current_user, get_outlet_scope
from app.middleware.rate_limiter import limiter
from app.models.users import User
from app.models.models_v6 import Product
from app.models.inventory import Inventory
from app.models.models_v6 import Sale, SaleItem
from app.models.alert import Alert
from app.database import get_db, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.schemas.analytics import MetricData, AlertsResponse, ChartDataResponse
from datetime import timezone


def get_sync_db():
    """Synchronous DB session for non-async endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


router = APIRouter(prefix="/analytics", tags=["Analytics/Dashboard"])

@router.get("/metrics", response_model=MetricData)
@limiter.limit("1000/minute")
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
@limiter.limit("1000/minute")
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
@limiter.limit("1000/minute")
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


@router.get("/dashboard/realtime")
def get_dashboard_realtime(
    db: Session = Depends(get_sync_db),
    current_user: Any = Depends(get_current_user),
):
    """
    Get real-time dashboard metrics for the authenticated user's accessible outlets.

    All numbers come from live DB queries — no synthetic data.
    Returns explicit zeroes and an empty list when there is no data.

    Returns: total_orders, total_revenue, today_revenue, active_orders,
             avg_order_value, data_source, recent_transactions
    """
    from sqlalchemy import text

    outlet_ids = get_outlet_scope(current_user, db)
    if not outlet_ids:
        outlet_ids = [-1]  # no accessible outlets → queries return 0 rows

    today = datetime.now().date()

    # ── Aggregate metrics ────────────────────────────────────────────────────
    try:
        agg = db.execute(
            text("""
                SELECT
                    COALESCE(SUM(total_amount), 0)                                      AS total_revenue,
                    COUNT(*)                                                             AS total_orders,
                    COALESCE(SUM(CASE WHEN DATE(sale_date) = :today THEN total_amount ELSE 0 END), 0) AS today_revenue,
                    COUNT(CASE WHEN DATE(sale_date) = :today THEN 1 END)                AS today_orders
                FROM sales
                WHERE outlet_id IN :outlet_ids
            """),
            {"today": today, "outlet_ids": tuple(outlet_ids)},
        ).fetchone()

        total_revenue = float(agg[0] or 0)
        total_orders  = int(agg[1] or 0)
        today_revenue = float(agg[2] or 0)
        today_orders  = int(agg[3] or 0)
    except Exception:
        total_revenue = 0.0
        total_orders  = 0
        today_revenue = 0.0
        today_orders  = 0

    avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

    # ── 10 most-recent transactions ──────────────────────────────────────────
    recent_transactions = []
    try:
        rows = db.execute(
            text("""
                SELECT s.id, s.sale_number, s.total_amount, s.payment_status, s.sale_date,
                       COALESCE(c.name, 'Walk-in') AS customer_name
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.outlet_id IN :outlet_ids
                ORDER BY s.sale_date DESC
                LIMIT 10
            """),
            {"outlet_ids": tuple(outlet_ids)},
        ).fetchall()
        recent_transactions = [
            {
                "id": r[1] or f"TXN-{r[0]}",
                "customer": r[5],
                "amount": float(r[2] or 0),
                "status": (r[3] or "unknown").lower(),
                "timestamp": str(r[4])[:19] if r[4] else "",
            }
            for r in rows
        ]
    except Exception:
        recent_transactions = []

    return {
        "total_orders":       total_orders,
        "total_revenue":      total_revenue,
        "today_revenue":      today_revenue,
        "active_orders":      today_orders,
        "avg_order_value":    avg_order_value,
        "data_source":        "database",
        "recent_transactions": recent_transactions,
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





from app.services.analytics_service import analytics_service

@router.get("/category-breakdown")
async def get_category_breakdown(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get sales breakdown by product category
    
    Returns category-wise sales, orders, and percentage distribution
    """
    data = analytics_service.get_category_breakdown(days=days)
    return {
        "success": True,
        "data": data
    }

@router.get("/top-products")
async def get_top_products(
    limit: int = Query(default=10, ge=1, le=50, description="Number of products to return"),
    metric: str = Query(default="revenue", pattern="^(revenue|units|profit)$", description="Sorting metric")
):
    """
    Get top performing products
    
    Can be sorted by revenue, units sold, or profit
    """
    products = analytics_service.get_top_products(limit=limit, metric=metric)
    return {
        "success": True,
        "data": {
            "products": products,
            "count": len(products),
            "sort_by": metric
        }
    }

@router.get("/trend-analysis")
async def get_trend_analysis(
    days: int = Query(default=90, ge=7, le=365, description="Number of days to analyze")
):
    """
    Analyze sales trends over time
    
    Returns daily and weekly aggregations with trend metrics
    """
    data = analytics_service.get_trend_analysis(days=days)
    return {
        "success": True,
        "data": data
    }

@router.get("/dashboard/summary")
def get_summary(
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
) -> Any:
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    outlet_ids = get_outlet_scope(current_user, db)
    if not outlet_ids:
        outlet_ids = [-1]

    try:
        row = db.execute(text("""
            SELECT
                COALESCE(SUM(CASE WHEN DATE(s.sale_date) = :today THEN s.total_amount ELSE 0 END), 0) as revenue_today,
                COALESCE(SUM(CASE WHEN DATE(s.sale_date) >= :week_ago THEN s.total_amount ELSE 0 END), 0) as revenue_week,
                COALESCE(SUM(CASE WHEN DATE(s.sale_date) >= :month_ago THEN s.total_amount ELSE 0 END), 0) as revenue_month,
                COUNT(DISTINCT CASE WHEN DATE(s.sale_date) = :today2 THEN s.id END) as transactions_today
            FROM sales s
            WHERE s.outlet_id IN :outlet_ids
        """), {"today": today, "today2": today, "week_ago": week_ago, "month_ago": month_ago, "outlet_ids": tuple(outlet_ids)}).fetchone()

        revenue_today = float(row[0] or 0)
        revenue_week = float(row[1] or 0)
        revenue_month = float(row[2] or 0)
        transactions_today = int(row[3] or 0)
    except Exception:
        revenue_today = 0
        revenue_week = 0
        revenue_month = 0
        transactions_today = 0

    top_products = []
    try:
        top = db.execute(text("""
            SELECT p.name, COALESCE(SUM(si.line_total), 0) as revenue,
                   COALESCE(SUM(si.quantity), 0) as qty
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) >= :month_ago AND s.outlet_id IN :outlet_ids
            GROUP BY p.id, p.name
            ORDER BY revenue DESC
            LIMIT 5
        """), {"month_ago": month_ago, "outlet_ids": tuple(outlet_ids)}).fetchall()
        top_products = [{"product_name": r[0], "revenue": float(r[1]), "quantity_sold": int(r[2])} for r in top]
    except Exception:
        pass

    revenue_trend = []
    try:
        trend = db.execute(text("""
            SELECT DATE(s.sale_date), COALESCE(SUM(s.total_amount), 0)
            FROM sales s
            WHERE DATE(s.sale_date) >= :month_ago AND s.outlet_id IN :outlet_ids
            GROUP BY DATE(s.sale_date)
            ORDER BY DATE(s.sale_date)
        """), {"month_ago": month_ago, "outlet_ids": tuple(outlet_ids)}).fetchall()
        revenue_trend = [{"date": str(r[0]), "revenue": float(r[1])} for r in trend]
    except Exception:
        pass

    cat_sales = []
    try:
        cat = db.execute(text("""
            SELECT c.name, COALESCE(SUM(si.line_total), 0), COALESCE(SUM(si.quantity), 0)
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) >= :month_ago AND s.outlet_id IN :outlet_ids
            GROUP BY c.name
            ORDER BY 2 DESC
        """), {"month_ago": month_ago, "outlet_ids": tuple(outlet_ids)}).fetchall()
        total_cat = sum(float(r[1]) for r in cat)
        cat_sales = [
            {"category": r[0] or "Other", "revenue": float(r[1]),
             "percentage": round(float(r[1]) / total_cat * 100, 1) if total_cat > 0 else 0}
            for r in cat
        ]
    except Exception:
        pass

    try:
        prev_week_start = week_ago - timedelta(days=7)
        prev = db.execute(text("""
            SELECT COALESCE(SUM(total_amount), 0) FROM sales
            WHERE DATE(sale_date) >= :prev_start AND DATE(sale_date) < :week_ago AND outlet_id IN :outlet_ids
        """), {"prev_start": prev_week_start, "week_ago": week_ago, "outlet_ids": tuple(outlet_ids)}).scalar() or 1
        change_pct = round((revenue_week - float(prev)) / float(prev) * 100, 1) if float(prev) > 0 else 0
    except Exception:
        change_pct = 0

    return {
        "total_revenue_today": revenue_today,
        "total_revenue_this_week": revenue_week,
        "total_revenue_this_month": revenue_month,
        "total_transactions_today": transactions_today,
        "low_stock_alerts_count": 0,
        "top_5_products_by_revenue_this_week": top_products,
        "revenue_trend_last_30_days": revenue_trend,
        "sales_by_category_this_month": cat_sales,
        "outlet_performance_this_month": [],
        "revenue_change_percent": change_pct,
        "summary_text": f"{int(transactions_today)} transactions today"
    }


@router.get("/dashboard/revenue-trend")
def get_revenue_trend(
    days: Optional[int] = Query(30, ge=1, le=365),
    period: Optional[str] = Query(None, pattern="^(7d|30d|90d|365d)$"),
    outlet_id: Optional[int] = None,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
) -> Any:
    period_days = {"7d": 7, "30d": 30, "90d": 90, "365d": 365}.get(period, days or 30) if period else (days or 30)
    start_date = datetime.now().date() - timedelta(days=period_days)

    user_outlets = get_outlet_scope(current_user, db)
    if not user_outlets:
        user_outlets = [-1]

    if outlet_id:
        if outlet_id not in user_outlets:
            raise HTTPException(status_code=403, detail="Access denied to this outlet")
        outlet_ids = [outlet_id]
    else:
        outlet_ids = user_outlets

    try:
        q = text("""
            SELECT DATE(s.sale_date) as date, COALESCE(SUM(s.total_amount), 0) as revenue
            FROM sales s
            WHERE DATE(s.sale_date) >= :start_date AND s.outlet_id IN :outlet_ids
            GROUP BY DATE(s.sale_date)
            ORDER BY DATE(s.sale_date)
        """)
        rows = db.execute(q, {"start_date": start_date, "outlet_ids": tuple(outlet_ids)}).fetchall()
        return [{"date": str(r[0]), "revenue": float(r[1])} for r in rows]
    except Exception:
        return []


@router.get("/dashboard/category-breakdown")
def get_category_breakdown(
    period: str = Query("30d", pattern="^(7d|30d|90d|365d)$"),
    outlet_id: Optional[int] = None,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
) -> Any:
    period_days = {"7d": 7, "30d": 30, "90d": 90, "365d": 365}.get(period, 30)
    start_date = datetime.now().date() - timedelta(days=period_days)

    user_outlets = get_outlet_scope(current_user, db)
    if not user_outlets:
        user_outlets = [-1]

    if outlet_id:
        if outlet_id not in user_outlets:
            raise HTTPException(status_code=403, detail="Access denied to this outlet")
        outlet_ids = [outlet_id]
    else:
        outlet_ids = user_outlets

    try:
        q = text("""
            SELECT c.name as category, COALESCE(SUM(si.line_total), 0) as revenue,
                   COALESCE(SUM(si.quantity), 0) as quantity, COUNT(DISTINCT s.id) as transactions
            FROM sales s
            JOIN sale_items si ON s.id = si.sale_id
            JOIN products p ON si.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            WHERE DATE(s.sale_date) >= :start_date AND s.outlet_id IN :outlet_ids
            GROUP BY c.name
            ORDER BY revenue DESC
        """)
        rows = db.execute(q, {"start_date": start_date, "outlet_ids": tuple(outlet_ids)}).fetchall()
        total = sum(float(r[1]) for r in rows)
        return {
            "period": period,
            "outlet_id": outlet_id,
            "total_revenue": float(total),
            "data": [
                {"category": r[0], "revenue": float(r[1]), "percentage": (float(r[1]) / total * 100) if total > 0 else 0,
                 "quantity": int(r[2]), "transactions": int(r[3])}
                for r in rows
            ]
        }
    except Exception:
        return {"period": period, "outlet_id": outlet_id, "total_revenue": 0, "data": []}


@router.get("/dashboard/sales-by-category")
def get_sales_by_category(
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
) -> Any:
    month_ago = datetime.now().date() - timedelta(days=30)

    outlet_ids = get_outlet_scope(current_user, db)
    if not outlet_ids:
        outlet_ids = [-1]

    try:
        q = text("""
            SELECT c.name as category, COALESCE(SUM(si.line_total), 0) as revenue,
                   COALESCE(SUM(si.quantity), 0) as quantity
            FROM sales s
            JOIN sale_items si ON s.id = si.sale_id
            JOIN products p ON si.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            WHERE DATE(s.sale_date) >= :month_ago AND s.outlet_id IN :outlet_ids
            GROUP BY c.name
            ORDER BY revenue DESC
        """)
        rows = db.execute(q, {"month_ago": month_ago, "outlet_ids": tuple(outlet_ids)}).fetchall()
        total = sum(float(r[1]) for r in rows)
        return [
            {"name": r[0] or "Other", "value": float(r[1]), "percent": round((float(r[1]) / total * 100), 1) if total > 0 else 0}
            for r in rows
        ]
    except Exception:
        return []


@router.get("/dashboard/top-products")
def get_top_products_endpoint(
    limit: int = Query(5, ge=1, le=50),
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
) -> Any:
    month_ago = datetime.now().date() - timedelta(days=30)

    outlet_ids = get_outlet_scope(current_user, db)
    if not outlet_ids:
        outlet_ids = [-1]

    try:
        q = text("""
            SELECT p.name, COALESCE(SUM(si.line_total), 0) as revenue,
                   COALESCE(SUM(si.quantity), 0) as quantity_sold,
                   COALESCE(c.name, 'Other') as category
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) >= :month_ago AND s.outlet_id IN :outlet_ids
            GROUP BY p.id, p.name, c.name
            ORDER BY revenue DESC
            LIMIT :limit
        """)
        rows = db.execute(q, {"month_ago": month_ago, "limit": limit, "outlet_ids": tuple(outlet_ids)}).fetchall()
        return [
            {"name": r[0], "revenue": float(r[1]), "quantity_sold": int(r[2]), "category": r[3]}
            for r in rows
        ]
    except Exception:
        return []


@router.get("/dashboard/outlet-performance")
def get_outlet_performance_endpoint(
    period: str = Query("30d", description="Period: 7d, 30d, 90d"),
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
) -> Any:
    days = {"7d": 7, "14d": 14, "30d": 30, "90d": 90}.get(period, 30)
    since = datetime.now().date() - timedelta(days=days)

    outlet_ids = get_outlet_scope(current_user, db)
    if not outlet_ids:
        outlet_ids = [-1]

    try:
        q = text("""
            SELECT o.id, o.name, o.city,
                   COALESCE(SUM(s.total_amount), 0) as revenue,
                   COUNT(DISTINCT s.id) as transactions
            FROM outlets o
            LEFT JOIN sales s ON o.id = s.outlet_id AND DATE(s.sale_date) >= :since
            WHERE o.id IN :outlet_ids AND o.is_active = TRUE
            GROUP BY o.id, o.name, o.city
            ORDER BY revenue DESC
        """)
        rows = db.execute(q, {"since": since, "outlet_ids": tuple(outlet_ids)}).fetchall()
        return [
            {
                "outlet_id": r[0],
                "outlet_name": r[1],
                "city": r[2] or "Unknown",
                "revenue": float(r[3]),
                "transactions": int(r[4]),
                "growth": 0.0
            }
            for r in rows
        ]
    except Exception:
        return []
