"""
Phase 4: Morning Dashboard

Real-time sales metrics, top products, pending orders, and business summary
for daily morning briefing and decision making
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from pydantic import BaseModel

from app.api.db.database import get_db
from app.api.db.models_v6 import Sale, SaleItem, Product, Customer, CreditAccount, Payment
from app.api.db.phase2_models import Invoice

router = APIRouter(prefix="/api/v4/dashboard", tags=["dashboard"])


# ==================== Request Models ====================

class DateRangeQuery(BaseModel):
    """Date range for analytics"""
    start_date: date
    end_date: date


# ==================== Response Models ====================

class MetricCard(BaseModel):
    """Single metric card"""
    title: str
    value: Any
    unit: Optional[str] = None
    change_percent: Optional[Decimal] = None
    trend: Optional[str] = None  # up, down, neutral
    timestamp: datetime


class TopProduct(BaseModel):
    """Top selling product"""
    rank: int
    product_id: int
    product_name: str
    quantity_sold: int
    revenue: Decimal
    percent_of_total: Decimal


class TopCustomer(BaseModel):
    """Top spending customer"""
    rank: int
    customer_id: int
    customer_name: str
    purchase_count: int
    total_spent: Decimal
    last_purchase: Optional[date] = None


class PendingOrder(BaseModel):
    """Pending or overdue order"""
    invoice_id: int
    invoice_number: str
    customer_name: str
    amount_due: Decimal
    days_overdue: int
    status: str


class MorningDashboardResponse(BaseModel):
    """Complete morning dashboard"""
    date: date
    summary_metrics: Dict[str, MetricCard]
    top_products: List[TopProduct]
    top_customers: List[TopCustomer]
    pending_orders: List[PendingOrder]
    payment_breakdown: Dict[str, Decimal]
    credit_health: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    forecast_summary: Optional[Dict[str, Any]] = None


# ==================== Morning Dashboard ====================

@router.get("/morning")
def get_morning_dashboard(
    business_id: int = Query(...),
    date_value: Optional[date] = Query(None),
    include_forecast: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Get morning dashboard with all key metrics
    
    Args:
        business_id: Business identifier
        date_value: Date to analyze (default: today)
        include_forecast: Include sales forecast
        
    Returns:
        Complete morning dashboard
    """
    try:
        if not date_value:
            date_value = date.today()
        
        # ==================== Sales Metrics ====================
        
        # Today's sales
        today_sales = db.query(
            func.count(Sale.id).label("count"),
            func.sum(Sale.total_amount).label("amount"),
            func.sum(Sale.gst_amount).label("gst")
        ).filter(
            func.date(Sale.sale_date) == date_value
        ).first()
        
        # Yesterday's sales for comparison
        yesterday = date_value - timedelta(days=1)
        yesterday_sales = db.query(
            func.sum(Sale.total_amount).label("amount")
        ).filter(
            func.date(Sale.sale_date) == yesterday
        ).first()
        
        today_amount = today_sales.amount or Decimal(0)
        yesterday_amount = yesterday_sales.amount or Decimal(0)
        sales_change = (
            ((today_amount - yesterday_amount) / yesterday_amount * 100)
            if yesterday_amount else Decimal(0)
        )
        
        # ==================== Payment Methods ====================
        
        payment_breakdown = db.query(
            Sale.payment_method,
            func.sum(Sale.amount_paid).label("amount"),
            func.count(Sale.id).label("count")
        ).filter(
            func.date(Sale.sale_date) == date_value
        ).group_by(Sale.payment_method).all()
        
        payment_dict = {
            (p.payment_method or "unknown"): float(p.amount or 0)
            for p in payment_breakdown
        }
        
        # ==================== Top Products ====================
        
        top_products_query = db.query(
            Product.id,
            Product.name,
            func.sum(SaleItem.quantity).label("qty"),
            func.sum(SaleItem.line_total).label("revenue")
        ).join(
            SaleItem, SaleItem.product_id == Product.id
        ).join(
            Sale, Sale.id == SaleItem.sale_id
        ).filter(
            func.date(Sale.sale_date) == date_value
        ).group_by(
            Product.id, Product.name
        ).order_by(
            func.sum(SaleItem.line_total).desc()
        ).limit(5).all()
        
        total_revenue = today_amount
        top_products = [
            TopProduct(
                rank=i+1,
                product_id=p.id,
                product_name=p.name,
                quantity_sold=int(p.qty or 0),
                revenue=Decimal(str(p.revenue or 0)),
                percent_of_total=(
                    Decimal(str(p.revenue or 0)) / total_revenue * 100
                    if total_revenue else Decimal(0)
                )
            )
            for i, p in enumerate(top_products_query)
        ]
        
        # ==================== Top Customers ====================
        
        top_customers_query = db.query(
            Customer.id,
            Customer.name,
            func.count(Sale.id).label("purchase_count"),
            func.sum(Sale.total_amount).label("total"),
            func.max(Sale.sale_date).label("last_purchase")
        ).join(
            Sale, Sale.customer_id == Customer.id
        ).filter(
            func.date(Sale.sale_date) == date_value
        ).group_by(
            Customer.id, Customer.name
        ).order_by(
            func.sum(Sale.total_amount).desc()
        ).limit(5).all()
        
        top_customers = [
            TopCustomer(
                rank=i+1,
                customer_id=c.id,
                customer_name=c.name,
                purchase_count=int(c.purchase_count or 0),
                total_spent=Decimal(str(c.total or 0)),
                last_purchase=c.last_purchase.date() if c.last_purchase else None
            )
            for i, c in enumerate(top_customers_query)
        ]
        
        # ==================== Pending Orders ====================
        
        pending = db.query(
            Invoice.id,
            Invoice.invoice_number,
            Customer.name,
            Invoice.grand_total,
            Invoice.due_date
        ).join(
            Customer, Customer.id == Invoice.customer_id
        ).filter(
            and_(
                Invoice.payment_status != "PAID",
                Invoice.invoice_date <= datetime.now()
            )
        ).order_by(
            Invoice.due_date.asc()
        ).limit(10).all()
        
        pending_orders = []
        for p in pending:
            days_overdue = (date_value - p.due_date).days if p.due_date else 0
            pending_orders.append(
                PendingOrder(
                    invoice_id=p.id,
                    invoice_number=p.invoice_number,
                    customer_name=p.name,
                    amount_due=Decimal(str(p.grand_total or 0)),
                    days_overdue=max(0, days_overdue),
                    status="overdue" if days_overdue > 0 else "pending"
                )
            )
        
        # ==================== Credit Health ====================
        
        credit_health = db.query(
            func.count(CreditAccount.id).label("total_accounts"),
            func.sum(CreditAccount.amount).label("total_credit"),
            func.sum(CreditAccount.amount_paid).label("amount_paid"),
            func.sum(CreditAccount.amount - CreditAccount.amount_paid).label("outstanding")
        ).filter(
            CreditAccount.status.in_(['pending', 'partial', 'overdue'])
        ).first()
        
        # ==================== Summary Metrics ====================
        
        summary_metrics = {
            "total_sales": MetricCard(
                title="Today's Sales",
                value=float(today_amount),
                unit="₹",
                change_percent=sales_change,
                trend="up" if sales_change > 0 else ("down" if sales_change < 0 else "neutral"),
                timestamp=datetime.now()
            ),
            "total_transactions": MetricCard(
                title="Total Transactions",
                value=int(today_sales.count or 0),
                change_percent=None,
                timestamp=datetime.now()
            ),
            "average_transaction": MetricCard(
                title="Avg Transaction",
                value=float(
                    today_amount / (today_sales.count or 1)
                    if today_sales.count else 0
                ),
                unit="₹",
                timestamp=datetime.now()
            ),
            "total_gst_collected": MetricCard(
                title="GST Collected",
                value=float(today_sales.gst or 0),
                unit="₹",
                timestamp=datetime.now()
            ),
            "outstanding_credit": MetricCard(
                title="Outstanding Credit",
                value=float(credit_health.outstanding or 0),
                unit="₹",
                timestamp=datetime.now()
            ),
            "pending_orders_count": MetricCard(
                title="Pending Orders",
                value=len(pending_orders),
                timestamp=datetime.now()
            ),
        }
        
        # ==================== Alerts ====================
        
        alerts = []
        
        if len(pending_orders) > 0:
            overdue_count = sum(1 for p in pending_orders if p.days_overdue > 0)
            if overdue_count > 0:
                alerts.append({
                    "level": "warning",
                    "message": f"{overdue_count} invoice(s) overdue",
                    "action": "Review credit accounts"
                })
        
        if (credit_health.outstanding or 0) > (today_amount * 2):
            alerts.append({
                "level": "alert",
                "message": "Outstanding credit exceeds 2x today's sales",
                "action": "Prioritize collections"
            })
        
        if today_amount < (yesterday_amount * 0.8) and yesterday_amount > 0:
            alerts.append({
                "level": "info",
                "message": "Sales down 20% vs yesterday",
                "action": "Check promotions or inventory"
            })
        
        return {
            "date": date_value,
            "summary_metrics": summary_metrics,
            "top_products": top_products,
            "top_customers": top_customers,
            "pending_orders": pending_orders[:5],  # Show top 5
            "payment_breakdown": payment_dict,
            "credit_health": {
                "total_accounts": int(credit_health.total_accounts or 0),
                "total_credit": float(credit_health.total_credit or 0),
                "amount_paid": float(credit_health.amount_paid or 0),
                "outstanding": float(credit_health.outstanding or 0)
            },
            "alerts": alerts,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Daily Summary ====================

@router.get("/daily-summary/{business_id}")
def get_daily_summary(
    business_id: int,
    date_value: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get simplified daily summary
    
    Args:
        business_id: Business identifier
        date_value: Date (default: today)
        
    Returns:
        Daily summary metrics
    """
    try:
        if not date_value:
            date_value = date.today()
        
        daily = db.query(
            func.count(Sale.id).label("transactions"),
            func.sum(Sale.total_amount).label("total_sales"),
            func.sum(Sale.gst_amount).label("gst"),
            func.count(func.distinct(Sale.customer_id)).label("unique_customers")
        ).filter(
            func.date(Sale.sale_date) == date_value
        ).first()
        
        return {
            "business_id": business_id,
            "date": date_value,
            "transactions": int(daily.transactions or 0),
            "total_sales": float(daily.total_sales or 0),
            "gst_collected": float(daily.gst or 0),
            "unique_customers": int(daily.unique_customers or 0),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Weekly Performance ====================

@router.get("/weekly-performance/{business_id}")
def get_weekly_performance(
    business_id: int,
    db: Session = Depends(get_db)
):
    """
    Get weekly performance metrics
    
    Args:
        business_id: Business identifier
        
    Returns:
        Weekly metrics by day
    """
    try:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        
        daily_data = db.query(
            func.date(Sale.sale_date).label("day"),
            func.count(Sale.id).label("transactions"),
            func.sum(Sale.total_amount).label("sales"),
            func.sum(Sale.gst_amount).label("gst")
        ).filter(
            and_(
                func.date(Sale.sale_date) >= week_start,
                func.date(Sale.sale_date) <= today
            )
        ).group_by(
            func.date(Sale.sale_date)
        ).order_by(
            func.date(Sale.sale_date)
        ).all()
        
        return {
            "business_id": business_id,
            "period": {
                "week_start": week_start.isoformat(),
                "week_end": today.isoformat()
            },
            "daily_performance": [
                {
                    "date": str(d.day),
                    "transactions": int(d.transactions or 0),
                    "sales": float(d.sales or 0),
                    "gst": float(d.gst or 0)
                }
                for d in daily_data
            ],
            "total_sales": sum(float(d.sales or 0) for d in daily_data),
            "total_gst": sum(float(d.gst or 0) for d in daily_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Category Performance ====================

@router.get("/category-performance/{business_id}")
def get_category_performance(
    business_id: int,
    date_value: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get performance by product category
    
    Args:
        business_id: Business identifier
        date_value: Date filter
        
    Returns:
        Category-wise metrics
    """
    try:
        if not date_value:
            date_value = date.today()
        
        from app.api.db.models_v6 import ProductCategory
        
        category_stats = db.query(
            ProductCategory.name,
            func.sum(SaleItem.quantity).label("qty"),
            func.sum(SaleItem.line_total).label("revenue"),
            func.count(func.distinct(Sale.id)).label("transactions")
        ).join(
            Product, Product.category_id == ProductCategory.id
        ).join(
            SaleItem, SaleItem.product_id == Product.id
        ).join(
            Sale, Sale.id == SaleItem.sale_id
        ).filter(
            func.date(Sale.sale_date) == date_value
        ).group_by(
            ProductCategory.name
        ).order_by(
            func.sum(SaleItem.line_total).desc()
        ).all()
        
        total_revenue = sum(float(c.revenue or 0) for c in category_stats)
        
        return {
            "business_id": business_id,
            "date": date_value,
            "categories": [
                {
                    "name": c.name,
                    "quantity": int(c.qty or 0),
                    "revenue": float(c.revenue or 0),
                    "percent_of_total": (
                        (float(c.revenue or 0) / total_revenue * 100)
                        if total_revenue else 0
                    ),
                    "transactions": int(c.transactions or 0)
                }
                for c in category_stats
            ],
            "total_revenue": total_revenue,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== KPI Summary ====================

@router.get("/kpi-summary/{business_id}")
def get_kpi_summary(
    business_id: int,
    days: int = Query(30),
    db: Session = Depends(get_db)
):
    """
    Get key performance indicators
    
    Args:
        business_id: Business identifier
        days: Period in days
        
    Returns:
        KPI metrics
    """
    try:
        start_date = date.today() - timedelta(days=days)
        
        stats = db.query(
            func.sum(Sale.total_amount).label("total_sales"),
            func.count(func.distinct(Sale.customer_id)).label("unique_customers"),
            func.count(Sale.id).label("transactions"),
            func.avg(Sale.total_amount).label("avg_transaction"),
            func.sum(Sale.gst_amount).label("total_gst")
        ).filter(
            and_(
                func.date(Sale.sale_date) >= start_date,
                func.date(Sale.sale_date) <= date.today()
            )
        ).first()
        
        return {
            "business_id": business_id,
            "period_days": days,
            "kpis": {
                "total_sales": float(stats.total_sales or 0),
                "unique_customers": int(stats.unique_customers or 0),
                "total_transactions": int(stats.transactions or 0),
                "average_transaction_value": float(stats.avg_transaction or 0),
                "total_gst": float(stats.total_gst or 0),
                "daily_average": float((stats.total_sales or 0) / days),
                "customer_repeat_rate": (
                    (int(stats.transactions or 0) / int(stats.unique_customers or 1))
                    if stats.unique_customers else 0
                )
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
