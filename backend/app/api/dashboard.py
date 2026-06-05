"""
Dashboard API Router - Real aggregated data from database
"""

from datetime import datetime, timedelta
from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract, select
from app.database import get_db
from app.models import User, SaleTransaction, Product, Inventory, Alert, Outlet
from app.api.deps import get_current_active_user, get_outlet_scope
from app.core.data_isolation import OutletDataAccess

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get dashboard summary for authenticated user's accessible outlets
    """
    allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(current_user, db)
    if not allowed_outlet_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No outlets accessible"
        )

    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    thirty_days_ago = today - timedelta(days=30)

    # Total revenue today
    revenue_today = db.query(func.sum(SaleTransaction.total_amount)).filter(
        SaleTransaction.outlet_id.in_(allowed_outlet_ids),
        func.date(SaleTransaction.transaction_at) == today
    ).scalar() or 0

    # Total revenue this week
    revenue_week = db.query(func.sum(SaleTransaction.total_amount)).filter(
        SaleTransaction.outlet_id.in_(allowed_outlet_ids),
        func.date(SaleTransaction.transaction_at) >= week_ago
    ).scalar() or 0

    # Total revenue this month
    revenue_month = db.query(func.sum(SaleTransaction.total_amount)).filter(
        SaleTransaction.outlet_id.in_(allowed_outlet_ids),
        func.date(SaleTransaction.transaction_at) >= month_ago
    ).scalar() or 0

    # Total transactions today
    transactions_today = db.query(func.count(SaleTransaction.id)).filter(
        SaleTransaction.outlet_id.in_(allowed_outlet_ids),
        func.date(SaleTransaction.transaction_at) == today
    ).scalar() or 0

    # Low stock alerts count (active/not acknowledged)
    low_stock_alerts = db.query(func.count(Alert.id)).filter(
        Alert.outlet_id.in_(allowed_outlet_ids),
        Alert.is_acknowledged == False
    ).scalar() or 0

    # Top 5 products by revenue this week
    top_products_result = db.query(
        Product.name,
        func.sum(SaleTransaction.total_amount).label("revenue"),
        func.sum(SaleTransaction.quantity).label("quantity_sold")
    ).join(SaleTransaction, Product.id == SaleTransaction.product_id).filter(
        SaleTransaction.outlet_id.in_(allowed_outlet_ids),
        func.date(SaleTransaction.transaction_at) >= week_ago
    ).group_by(Product.id, Product.name).order_by(
        func.sum(SaleTransaction.total_amount).desc()
    ).limit(5).all()

    top_products = [
        {
            "product_name": row[0],
            "revenue": float(row[1]) if row[1] else 0,
            "quantity_sold": int(row[2]) if row[2] else 0
        }
        for row in top_products_result
    ]

    # Revenue trend last 30 days
    trend_result = db.query(
        func.date(SaleTransaction.transaction_at).label("date"),
        func.sum(SaleTransaction.total_amount).label("revenue")
    ).filter(
        SaleTransaction.outlet_id.in_(allowed_outlet_ids),
        func.date(SaleTransaction.transaction_at) >= thirty_days_ago
    ).group_by(func.date(SaleTransaction.transaction_at)).order_by(
        func.date(SaleTransaction.transaction_at)
    ).all()

    revenue_trend = [
        {
            "date": str(row[0]),
            "revenue": float(row[1]) if row[1] else 0
        }
        for row in trend_result
    ]

    # Sales by category this month
    category_result = db.query(
        Product.category,
        func.sum(SaleTransaction.total_amount).label("revenue"),
        func.sum(SaleTransaction.quantity).label("quantity")
    ).join(SaleTransaction, Product.id == SaleTransaction.product_id).filter(
        SaleTransaction.outlet_id.in_(allowed_outlet_ids),
        func.date(SaleTransaction.transaction_at) >= month_ago
    ).group_by(Product.category).order_by(
        func.sum(SaleTransaction.total_amount).desc()
    ).all()

    total_revenue_month = sum(float(row[1]) if row[1] else 0 for row in category_result)
    sales_by_category = [
        {
            "category": row[0],
            "revenue": float(row[1]) if row[1] else 0,
            "percentage": (float(row[1]) / total_revenue_month * 100) if total_revenue_month > 0 else 0
        }
        for row in category_result
    ]

    # Outlet performance this month (superadmin only)
    outlet_performance = []
    if current_user.role == "super_admin":
        outlet_perf_result = db.query(
            Outlet.id,
            Outlet.name,
            func.sum(SaleTransaction.total_amount).label("revenue"),
            func.count(SaleTransaction.id).label("transactions")
        ).join(SaleTransaction, Outlet.id == SaleTransaction.outlet_id).filter(
            Outlet.id.in_(outlet_scope),
            func.date(SaleTransaction.transaction_at) >= month_ago
        ).group_by(Outlet.id, Outlet.name).order_by(
            func.sum(SaleTransaction.total_amount).desc()
        ).all()

        outlet_performance = [
            {
                "outlet_name": row[1],
                "revenue": float(row[2]) if row[2] else 0,
                "transactions": int(row[3]) if row[3] else 0
            }
            for row in outlet_perf_result
        ]

    return {
        "total_revenue_today": float(revenue_today),
        "total_revenue_this_week": float(revenue_week),
        "total_revenue_this_month": float(revenue_month),
        "total_transactions_today": int(transactions_today),
        "low_stock_alerts_count": int(low_stock_alerts),
        "top_5_products_by_revenue_this_week": top_products,
        "revenue_trend_last_30_days": revenue_trend,
        "sales_by_category_this_month": sales_by_category,
        "outlet_performance_this_month": outlet_performance
    }


@router.get("/outlet/{outlet_id}/summary")
async def get_outlet_summary(
    outlet_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get dashboard summary for a specific outlet.
    Superadmin can query any outlet. Manager can only query their own.
    """
    if not OutletDataAccess.can_access_outlet(outlet_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this outlet"
        )

    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    thirty_days_ago = today - timedelta(days=30)

    # Total revenue today
    revenue_today = db.query(func.sum(SaleTransaction.total_amount)).filter(
        SaleTransaction.outlet_id == outlet_id,
        func.date(SaleTransaction.transaction_at) == today
    ).scalar() or 0

    # Total revenue this week
    revenue_week = db.query(func.sum(SaleTransaction.total_amount)).filter(
        SaleTransaction.outlet_id == outlet_id,
        func.date(SaleTransaction.transaction_at) >= week_ago
    ).scalar() or 0

    # Total revenue this month
    revenue_month = db.query(func.sum(SaleTransaction.total_amount)).filter(
        SaleTransaction.outlet_id == outlet_id,
        func.date(SaleTransaction.transaction_at) >= month_ago
    ).scalar() or 0

    # Total transactions today
    transactions_today = db.query(func.count(SaleTransaction.id)).filter(
        SaleTransaction.outlet_id == outlet_id,
        func.date(SaleTransaction.transaction_at) == today
    ).scalar() or 0

    # Low stock alerts count
    low_stock_alerts = db.query(func.count(Alert.id)).filter(
        Alert.outlet_id == outlet_id,
        Alert.is_acknowledged == False
    ).scalar() or 0

    # Top 5 products by revenue this week
    top_products_result = db.query(
        Product.name,
        func.sum(SaleTransaction.total_amount).label("revenue"),
        func.sum(SaleTransaction.quantity).label("quantity_sold")
    ).join(SaleTransaction, Product.id == SaleTransaction.product_id).filter(
        SaleTransaction.outlet_id == outlet_id,
        func.date(SaleTransaction.transaction_at) >= week_ago
    ).group_by(Product.id, Product.name).order_by(
        func.sum(SaleTransaction.total_amount).desc()
    ).limit(5).all()

    top_products = [
        {
            "product_name": row[0],
            "revenue": float(row[1]) if row[1] else 0,
            "quantity_sold": int(row[2]) if row[2] else 0
        }
        for row in top_products_result
    ]

    # Revenue trend last 30 days
    trend_result = db.query(
        func.date(SaleTransaction.transaction_at).label("date"),
        func.sum(SaleTransaction.total_amount).label("revenue")
    ).filter(
        SaleTransaction.outlet_id == outlet_id,
        func.date(SaleTransaction.transaction_at) >= thirty_days_ago
    ).group_by(func.date(SaleTransaction.transaction_at)).order_by(
        func.date(SaleTransaction.transaction_at)
    ).all()

    revenue_trend = [
        {
            "date": str(row[0]),
            "revenue": float(row[1]) if row[1] else 0
        }
        for row in trend_result
    ]

    # Sales by category this month
    category_result = db.query(
        Product.category,
        func.sum(SaleTransaction.total_amount).label("revenue"),
        func.sum(SaleTransaction.quantity).label("quantity")
    ).join(SaleTransaction, Product.id == SaleTransaction.product_id).filter(
        SaleTransaction.outlet_id == outlet_id,
        func.date(SaleTransaction.transaction_at) >= month_ago
    ).group_by(Product.category).order_by(
        func.sum(SaleTransaction.total_amount).desc()
    ).all()

    total_revenue_month = sum(float(row[1]) if row[1] else 0 for row in category_result)
    sales_by_category = [
        {
            "category": row[0],
            "revenue": float(row[1]) if row[1] else 0,
            "percentage": (float(row[1]) / total_revenue_month * 100) if total_revenue_month > 0 else 0
        }
        for row in category_result
    ]

    return {
        "total_revenue_today": float(revenue_today),
        "total_revenue_this_week": float(revenue_week),
        "total_revenue_this_month": float(revenue_month),
        "total_transactions_today": int(transactions_today),
        "low_stock_alerts_count": int(low_stock_alerts),
        "top_5_products_by_revenue_this_week": top_products,
        "revenue_trend_last_30_days": revenue_trend,
        "sales_by_category_this_month": sales_by_category,
        "outlet_performance_this_month": []
    }


@router.get("/revenue-trend")
async def get_revenue_trend(
    period: str = Query("30d", regex="^(7d|30d|90d|365d)$"),
    outlet_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get revenue trend for a period.
    Period: 7d (7 days), 30d (30 days), 90d (90 days), 365d (1 year)
    If outlet_id not provided, returns data for all user's accessible outlets.
    """
    # Parse period
    period_days = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "365d": 365
    }.get(period, 30)

    start_date = datetime.now().date() - timedelta(days=period_days)

    # Get outlet scope
    allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(current_user, db)
    if not allowed_outlet_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No outlets accessible"
        )

    # If outlet_id specified, verify access
    if outlet_id:
        if not OutletDataAccess.can_access_outlet(outlet_id, current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this outlet"
            )
        outlets_filter = [outlet_id]
    else:
        outlets_filter = allowed_outlet_ids

    # Query revenue trend
    trend_result = db.query(
        func.date(SaleTransaction.transaction_at).label("date"),
        func.sum(SaleTransaction.total_amount).label("revenue")
    ).filter(
        SaleTransaction.outlet_id.in_(outlets_filter),
        func.date(SaleTransaction.transaction_at) >= start_date
    ).group_by(func.date(SaleTransaction.transaction_at)).order_by(
        func.date(SaleTransaction.transaction_at)
    ).all()

    revenue_data = [
        {
            "date": str(row[0]),
            "revenue": float(row[1]) if row[1] else 0
        }
        for row in trend_result
    ]

    return {
        "period": period,
        "outlet_id": outlet_id,
        "data": revenue_data
    }


@router.get("/category-breakdown")
async def get_category_breakdown(
    period: str = Query("30d", regex="^(7d|30d|90d|365d)$"),
    outlet_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get sales breakdown by category for a period.
    Period: 7d, 30d, 90d, 365d
    If outlet_id not provided, returns data for all user's accessible outlets.
    """
    # Parse period
    period_days = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "365d": 365
    }.get(period, 30)

    start_date = datetime.now().date() - timedelta(days=period_days)

    # Get outlet scope
    allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(current_user, db)
    if not allowed_outlet_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No outlets accessible"
        )

    # If outlet_id specified, verify access
    if outlet_id:
        if not OutletDataAccess.can_access_outlet(outlet_id, current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this outlet"
            )
        outlets_filter = [outlet_id]
    else:
        outlets_filter = allowed_outlet_ids

    # Query category breakdown
    category_result = db.query(
        Product.category,
        func.sum(SaleTransaction.total_amount).label("revenue"),
        func.sum(SaleTransaction.quantity).label("quantity"),
        func.count(SaleTransaction.id).label("transactions")
    ).join(SaleTransaction, Product.id == SaleTransaction.product_id).filter(
        SaleTransaction.outlet_id.in_(outlets_filter),
        func.date(SaleTransaction.transaction_at) >= start_date
    ).group_by(Product.category).order_by(
        func.sum(SaleTransaction.total_amount).desc()
    ).all()

    total_revenue = sum(float(row[1]) if row[1] else 0 for row in category_result)

    category_data = [
        {
            "category": row[0],
            "revenue": float(row[1]) if row[1] else 0,
            "percentage": (float(row[1]) / total_revenue * 100) if total_revenue > 0 else 0,
            "quantity": int(row[2]) if row[2] else 0,
            "transactions": int(row[3]) if row[3] else 0
        }
        for row in category_result
    ]

    return {
        "period": period,
        "outlet_id": outlet_id,
        "total_revenue": float(total_revenue),
        "data": category_data
    }
