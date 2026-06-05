"""
Sales Analytics Router - Dashboard queries and metrics
Provides comprehensive sales analytics for the R-DIOS dashboard
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text, desc, and_, or_, extract
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from decimal import Decimal
import logging
from fastapi import Request

from app.core.data_isolation import OutletDataAccess

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics/sales", tags=["Sales Analytics"])


# ============================================================
# PYDANTIC MODELS
# ============================================================

class DateRangeRequest(BaseModel):
    start_date: date
    end_date: date
    
class RevenueMetrics(BaseModel):
    total_revenue: float
    total_orders: int
    avg_order_value: float
    total_gst: float
    total_discount: float
    net_revenue: float
    
class DailyRevenue(BaseModel):
    date: date
    revenue: float
    orders: int
    avg_order_value: float
    
class CategoryRevenue(BaseModel):
    category: str
    revenue: float
    orders: int
    units_sold: int
    percentage: float

class TopProduct(BaseModel):
    product_id: int
    name: str
    category: str
    units_sold: int
    revenue: float
    
class PaymentMethodBreakdown(BaseModel):
    method: str
    amount: float
    count: int
    percentage: float

class HourlyPattern(BaseModel):
    hour: int
    orders: int
    revenue: float

class CausalFactorImpact(BaseModel):
    factor: str
    affected_orders: int
    avg_order_value: float
    total_revenue: float
    impact_vs_baseline: float


# ============================================================
# DASHBOARD ENDPOINTS
# ============================================================

@router.get("/summary", response_model=Dict[str, Any])
@cache_response(ttl_seconds=300)
async def get_sales_summary(
    request: Request,
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive sales summary for dashboard
    Default: Last 30 days
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    query = text("""
        SELECT
            COUNT(*) as total_orders,
            COALESCE(SUM(total_amount), 0) as total_revenue,
            COALESCE(AVG(total_amount), 0) as avg_order_value,
            COALESCE(SUM(gst_amount), 0) as total_gst,
            COALESCE(SUM(discount_amount), 0) as total_discount,
            COUNT(DISTINCT customer_id) as unique_customers,
            COUNT(CASE WHEN payment_status = 'paid' THEN 1 END) as paid_orders,
            COUNT(CASE WHEN payment_status = 'pending' THEN 1 END) as pending_orders,
            COUNT(CASE WHEN is_holiday = true THEN 1 END) as holiday_orders
        FROM sales
        WHERE sale_date >= :start_date AND sale_date < :end_date
    """)

    # Apply outlet access control
    allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(current_user)
    if allowed_outlet_ids is not None:
        if not allowed_outlet_ids:
            # User has no outlet access
            return {
                "total_orders": 0,
                "total_revenue": 0,
                "avg_order_value": 0,
                "total_gst": 0,
                "total_discount": 0,
                "unique_customers": 0,
                "paid_orders": 0,
                "pending_orders": 0,
                "holiday_orders": 0,
                "period_comparison": {
                    "revenue_change_pct": 0,
                    "orders_change_pct": 0
                }
            }

        outlet_filter = " AND outlet_id = ANY(:outlet_ids)"
        query = text(str(query) + outlet_filter)
        params = {"start_date": start_date, "end_date": end_date + timedelta(days=1), "outlet_ids": allowed_outlet_ids}
    else:
        params = {"start_date": start_date, "end_date": end_date + timedelta(days=1)}

    result = db.execute(query, params)
    row = result.fetchone()
    
    # Get previous period for comparison
    prev_start = start_date - (end_date - start_date)
    prev_end = start_date
    
    prev_result = db.execute(query, {"start_date": prev_start, "end_date": prev_end})
    prev_row = prev_result.fetchone()
    
    # Calculate growth rates
    def growth_rate(current, previous):
        if previous and previous > 0:
            return round((current - previous) / previous * 100, 1)
        return 0
    
    return {
        "period": {"start": str(start_date), "end": str(end_date)},
        "metrics": {
            "total_orders": row.total_orders or 0,
            "total_revenue": float(row.total_revenue or 0),
            "avg_order_value": round(float(row.avg_order_value or 0), 2),
            "total_gst": float(row.total_gst or 0),
            "total_discount": float(row.total_discount or 0),
            "unique_customers": row.unique_customers or 0,
            "paid_orders": row.paid_orders or 0,
            "pending_orders": row.pending_orders or 0,
            "holiday_orders": row.holiday_orders or 0
        },
        "growth": {
            "orders": growth_rate(row.total_orders or 0, prev_row.total_orders if prev_row else 0),
            "revenue": growth_rate(float(row.total_revenue or 0), float(prev_row.total_revenue or 0) if prev_row else 0),
            "aov": growth_rate(float(row.avg_order_value or 0), float(prev_row.avg_order_value or 0) if prev_row else 0)
        }
    }


@router.get("/daily-trend", response_model=List[Dict[str, Any]])
@cache_response(ttl_seconds=300)
async def get_daily_revenue_trend(
    request: Request,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get daily revenue trend for charts"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    query = text("""
        SELECT 
            DATE(sale_date) as date,
            COUNT(*) as orders,
            SUM(total_amount) as revenue,
            AVG(total_amount) as avg_order_value,
            SUM(gst_amount) as gst,
            BOOL_OR(is_holiday) as has_holiday
        FROM sales
        WHERE sale_date >= :start_date AND sale_date < :end_date
        GROUP BY DATE(sale_date)
        ORDER BY date
    """)
    
    result = db.execute(query, {"start_date": start_date, "end_date": end_date + timedelta(days=1)})
    
    return [
        {
            "date": str(row.date),
            "orders": row.orders,
            "revenue": float(row.revenue or 0),
            "avg_order_value": round(float(row.avg_order_value or 0), 2),
            "gst": float(row.gst or 0),
            "has_holiday": row.has_holiday or False
        }
        for row in result.fetchall()
    ]


@router.get("/by-category", response_model=List[Dict[str, Any]])
@cache_response(ttl_seconds=300)
async def get_sales_by_category(
    request: Request,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get sales breakdown by product category"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    query = text("""
        SELECT 
            COALESCE(p.category_id, 0) as category_id,
            COALESCE(pc.name, 'Unknown') as category_name,
            COUNT(DISTINCT s.id) as orders,
            SUM(si.quantity) as units_sold,
            SUM(si.line_total) as revenue
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.id
        LEFT JOIN products p ON si.product_id = p.id
        LEFT JOIN product_categories pc ON p.category_id = pc.id
        WHERE s.sale_date >= :start_date AND s.sale_date < :end_date
        GROUP BY p.category_id, pc.name
        ORDER BY revenue DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {
        "start_date": start_date,
        "end_date": end_date + timedelta(days=1),
        "limit": limit
    })
    
    rows = result.fetchall()
    total_revenue = sum(float(row.revenue or 0) for row in rows)
    
    return [
        {
            "category_id": row.category_id,
            "category": row.category_name,
            "orders": row.orders,
            "units_sold": row.units_sold or 0,
            "revenue": float(row.revenue or 0),
            "percentage": round(float(row.revenue or 0) / total_revenue * 100, 1) if total_revenue > 0 else 0
        }
        for row in rows
    ]


@router.get("/top-products", response_model=List[Dict[str, Any]])
@cache_response(ttl_seconds=300)
async def get_top_products(
    request: Request,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    sort_by: str = Query("revenue", pattern="^(revenue|units|orders)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get top selling products"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    order_by = {
        "revenue": "revenue DESC",
        "units": "units_sold DESC",
        "orders": "orders DESC"
    }.get(sort_by, "revenue DESC")
    
    query = text(f"""
        SELECT 
            p.id as product_id,
            p.name,
            p.sku,
            COALESCE(pc.name, 'Unknown') as category,
            p.selling_price,
            p.cost_price,
            COUNT(DISTINCT si.sale_id) as orders,
            SUM(si.quantity) as units_sold,
            SUM(si.line_total) as revenue,
            SUM(si.line_total) - (SUM(si.quantity) * p.cost_price) as profit
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.id
        JOIN products p ON si.product_id = p.id
        LEFT JOIN product_categories pc ON p.category_id = pc.id
        WHERE s.sale_date >= :start_date AND s.sale_date < :end_date
        GROUP BY p.id, p.name, p.sku, pc.name, p.selling_price, p.cost_price
        ORDER BY {order_by}
        LIMIT :limit
    """)
    
    result = db.execute(query, {
        "start_date": start_date,
        "end_date": end_date + timedelta(days=1),
        "limit": limit
    })
    
    return [
        {
            "product_id": row.product_id,
            "name": row.name,
            "sku": row.sku,
            "category": row.category,
            "selling_price": float(row.selling_price or 0),
            "cost_price": float(row.cost_price or 0),
            "orders": row.orders,
            "units_sold": row.units_sold or 0,
            "revenue": float(row.revenue or 0),
            "profit": float(row.profit or 0)
        }
        for row in result.fetchall()
    ]


@router.get("/payment-methods", response_model=List[Dict[str, Any]])
async def get_payment_method_breakdown(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get payment method distribution"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    query = text("""
        SELECT 
            COALESCE(payment_method, 'unknown') as method,
            COUNT(*) as order_count,
            SUM(total_amount) as total_amount,
            AVG(total_amount) as avg_amount
        FROM sales
        WHERE sale_date >= :start_date AND sale_date < :end_date
        GROUP BY payment_method
        ORDER BY total_amount DESC
    """)
    
    result = db.execute(query, {"start_date": start_date, "end_date": end_date + timedelta(days=1)})
    
    rows = result.fetchall()
    total = sum(float(row.total_amount or 0) for row in rows)
    
    return [
        {
            "method": row.method,
            "count": row.order_count,
            "amount": float(row.total_amount or 0),
            "avg_amount": round(float(row.avg_amount or 0), 2),
            "percentage": round(float(row.total_amount or 0) / total * 100, 1) if total > 0 else 0
        }
        for row in rows
    ]


@router.get("/hourly-pattern", response_model=List[Dict[str, Any]])
async def get_hourly_sales_pattern(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get hourly sales pattern for staffing optimization"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    query = text("""
        SELECT 
            EXTRACT(HOUR FROM sale_date) as hour,
            COUNT(*) as orders,
            SUM(total_amount) as revenue,
            AVG(total_amount) as avg_order_value
        FROM sales
        WHERE sale_date >= :start_date AND sale_date < :end_date
        GROUP BY EXTRACT(HOUR FROM sale_date)
        ORDER BY hour
    """)
    
    result = db.execute(query, {"start_date": start_date, "end_date": end_date + timedelta(days=1)})
    
    return [
        {
            "hour": int(row.hour),
            "orders": row.orders,
            "revenue": float(row.revenue or 0),
            "avg_order_value": round(float(row.avg_order_value or 0), 2)
        }
        for row in result.fetchall()
    ]


@router.get("/weekly-pattern", response_model=List[Dict[str, Any]])
async def get_weekly_sales_pattern(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get weekly sales pattern (day of week analysis)"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)
    
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    query = text("""
        SELECT 
            EXTRACT(DOW FROM sale_date) as day_of_week,
            COUNT(*) as orders,
            SUM(total_amount) as revenue,
            AVG(total_amount) as avg_order_value
        FROM sales
        WHERE sale_date >= :start_date AND sale_date < :end_date
        GROUP BY EXTRACT(DOW FROM sale_date)
        ORDER BY day_of_week
    """)
    
    result = db.execute(query, {"start_date": start_date, "end_date": end_date + timedelta(days=1)})
    
    return [
        {
            "day_of_week": int(row.day_of_week),
            "day_name": day_names[int(row.day_of_week) % 7],
            "orders": row.orders,
            "revenue": float(row.revenue or 0),
            "avg_order_value": round(float(row.avg_order_value or 0), 2)
        }
        for row in result.fetchall()
    ]


# ============================================================
# CAUSAL ANALYSIS ENDPOINTS (Thesis-specific)
# ============================================================

@router.get("/causal/holiday-impact", response_model=Dict[str, Any])
async def get_holiday_impact_analysis(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze impact of holidays on sales (for causal inference)
    Compares holiday vs non-holiday sales
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=365)
    
    query = text("""
        SELECT 
            is_holiday,
            holiday_name,
            COUNT(*) as orders,
            SUM(total_amount) as revenue,
            AVG(total_amount) as avg_order_value,
            COUNT(DISTINCT customer_id) as unique_customers
        FROM sales
        WHERE sale_date >= :start_date AND sale_date < :end_date
        GROUP BY is_holiday, holiday_name
        ORDER BY is_holiday DESC, revenue DESC
    """)
    
    result = db.execute(query, {"start_date": start_date, "end_date": end_date + timedelta(days=1)})
    rows = result.fetchall()
    
    # Separate holiday and non-holiday data
    holiday_data = [r for r in rows if r.is_holiday]
    non_holiday = next((r for r in rows if not r.is_holiday), None)
    
    baseline_aov = float(non_holiday.avg_order_value) if non_holiday else 0
    
    return {
        "period": {"start": str(start_date), "end": str(end_date)},
        "baseline": {
            "orders": non_holiday.orders if non_holiday else 0,
            "revenue": float(non_holiday.revenue or 0) if non_holiday else 0,
            "avg_order_value": baseline_aov
        },
        "holidays": [
            {
                "name": row.holiday_name or "Unknown Holiday",
                "orders": row.orders,
                "revenue": float(row.revenue or 0),
                "avg_order_value": round(float(row.avg_order_value or 0), 2),
                "impact_percent": round((float(row.avg_order_value or 0) - baseline_aov) / baseline_aov * 100, 1) if baseline_aov > 0 else 0
            }
            for row in holiday_data
        ],
        "summary": {
            "total_holiday_orders": sum(r.orders for r in holiday_data),
            "total_holiday_revenue": sum(float(r.revenue or 0) for r in holiday_data),
            "avg_holiday_aov": round(sum(float(r.avg_order_value or 0) for r in holiday_data) / len(holiday_data), 2) if holiday_data else 0
        }
    }


@router.get("/causal/weather-impact", response_model=Dict[str, Any])
async def get_weather_impact_analysis(
    city: str = Query("Mumbai", description="City for weather data"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze impact of weather on sales (for causal inference)
    Correlates sales with weather conditions
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=365)
    
    query = text("""
        SELECT 
            w.condition,
            COUNT(s.id) as orders,
            SUM(s.total_amount) as revenue,
            AVG(s.total_amount) as avg_order_value,
            AVG(w.temperature_avg) as avg_temperature,
            AVG(w.precipitation_mm) as avg_precipitation
        FROM sales s
        JOIN weather_data w ON DATE(s.sale_date) = w.date AND w.city = :city
        WHERE s.sale_date >= :start_date AND s.sale_date < :end_date
        GROUP BY w.condition
        ORDER BY revenue DESC
    """)
    
    result = db.execute(query, {
        "city": city,
        "start_date": start_date,
        "end_date": end_date + timedelta(days=1)
    })
    rows = result.fetchall()
    
    # Find baseline (sunny days typically)
    sunny = next((r for r in rows if r.condition == 'sunny'), rows[0] if rows else None)
    baseline_aov = float(sunny.avg_order_value) if sunny else 0
    
    return {
        "city": city,
        "period": {"start": str(start_date), "end": str(end_date)},
        "by_condition": [
            {
                "condition": row.condition,
                "orders": row.orders,
                "revenue": float(row.revenue or 0),
                "avg_order_value": round(float(row.avg_order_value or 0), 2),
                "avg_temperature": round(float(row.avg_temperature or 0), 1),
                "avg_precipitation": round(float(row.avg_precipitation or 0), 1),
                "impact_percent": round((float(row.avg_order_value or 0) - baseline_aov) / baseline_aov * 100, 1) if baseline_aov > 0 else 0
            }
            for row in rows
        ]
    }


@router.get("/causal/channel-comparison", response_model=Dict[str, Any])
async def get_channel_comparison(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Compare sales across channels (offline, online, whatsapp)"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    query = text("""
        SELECT 
            COALESCE(channel, 'unknown') as channel,
            COUNT(*) as orders,
            SUM(total_amount) as revenue,
            AVG(total_amount) as avg_order_value,
            COUNT(DISTINCT customer_id) as unique_customers
        FROM sales
        WHERE sale_date >= :start_date AND sale_date < :end_date
        GROUP BY channel
        ORDER BY revenue DESC
    """)
    
    result = db.execute(query, {"start_date": start_date, "end_date": end_date + timedelta(days=1)})
    rows = result.fetchall()
    total_revenue = sum(float(row.revenue or 0) for row in rows)
    
    return {
        "period": {"start": str(start_date), "end": str(end_date)},
        "channels": [
            {
                "channel": row.channel,
                "orders": row.orders,
                "revenue": float(row.revenue or 0),
                "avg_order_value": round(float(row.avg_order_value or 0), 2),
                "unique_customers": row.unique_customers,
                "percentage": round(float(row.revenue or 0) / total_revenue * 100, 1) if total_revenue > 0 else 0
            }
            for row in rows
        ]
    }
