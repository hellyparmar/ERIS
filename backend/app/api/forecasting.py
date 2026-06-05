"""
Forecasting API Router - Prophet-based sales and inventory forecasting
"""

from datetime import datetime, timedelta
from typing import Any, Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, select
import json

from app.database import get_db
from app.models import User, SaleTransaction, Inventory, Product, Outlet, Forecast
from app.api.deps import get_current_active_user
from app.core.data_isolation import OutletDataAccess

router = APIRouter(prefix="/api/v1/forecasting", tags=["forecasting"])

# Try to import Prophet
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

import pandas as pd
import numpy as np


def check_prophet_available():
    """Verify Prophet is available"""
    if not PROPHET_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Forecasting service initializing"
        )


@router.get("/sales")
async def forecast_sales(
    outlet_id: int = Query(...),
    product_id: Optional[int] = None,
    forecast_days: int = Query(30, regex="^(7|14|30|90)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Forecast sales using Prophet model with caching.
    Checks cache first (6-hour window), trains new model if needed.
    Returns forecast with confidence intervals and accuracy metrics.
    """
    check_prophet_available()
    if not OutletDataAccess.can_access_outlet(outlet_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this outlet"
        )

    # Check cache: existing forecast created in last 6 hours
    six_hours_ago = datetime.now() - timedelta(hours=6)

    result = await db.execute(select(Forecast).where(Forecast.outlet_id == outlet_id,
        Forecast.forecast_type == "revenue",
        Forecast.generated_at >= six_hours_ago
    )

    if product_id:
        cache_query = cache_query.filter(Forecast.product_id == product_id)
    else:
        cache_query = cache_query.filter(Forecast.product_id == None)

    cached_forecasts = cache_query.all()

    if cached_forecasts and len(cached_forecasts) > 0:
        # Return cached forecast
        forecast_items = [
            {
                "date": str(f.forecast_date),
                "predicted_value": f.forecast_value,
                "confidence_lower": f.lower_bound or 0,
                "confidence_upper": f.upper_bound or 0
            }
            for f in sorted(cached_forecasts, key=lambda x: x.forecast_date)
        ]

        predicted_values = [f["predicted_value"] for f in forecast_items]
        actual_values = [f.actual_value for f in cached_forecasts if f.actual_value]

        mae = calculate_mae(predicted_values, actual_values) if actual_values else 0
        mape = calculate_mape(predicted_values, actual_values) if actual_values else 0

        return {
            "outlet_id": outlet_id,
            "product_id": product_id,
            "forecast_days": forecast_days,
            "from_cache": True,
            "dates": [f["date"] for f in forecast_items],
            "predicted_values": predicted_values,
            "confidence_lower": [f["confidence_lower"] for f in forecast_items],
            "confidence_upper": [f["confidence_upper"] for f in forecast_items],
            "model_accuracy_metrics": {
                "mae": round(mae, 2),
                "mape": round(mape, 2)
            },
            "factors_impact": {
                "holiday_impact_pct": 0.0,
                "weekend_impact_pct": 0.0
            }
        }

    # No cache: train new model
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)

    if product_id:
        sales_data = db.query(
            func.date(SaleTransaction.transaction_at).label("date"),
            func.sum(SaleTransaction.quantity).label("qty")
        ).filter(
            SaleTransaction.outlet_id == outlet_id,
            SaleTransaction.product_id == product_id,
            func.date(SaleTransaction.transaction_at) >= start_date,
            func.date(SaleTransaction.transaction_at) <= end_date
        ).group_by(func.date(SaleTransaction.transaction_at)).all()
    else:
        sales_data = db.query(
            func.date(SaleTransaction.transaction_at).label("date"),
            func.sum(SaleTransaction.total_amount).label("revenue")
        ).filter(
            SaleTransaction.outlet_id == outlet_id,
            func.date(SaleTransaction.transaction_at) >= start_date,
            func.date(SaleTransaction.transaction_at) <= end_date
        ).group_by(func.date(SaleTransaction.transaction_at)).all()

    if not sales_data or len(sales_data) < 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient historical data for forecasting (need at least 30 days)"
        )

    # Prepare dataframe for Prophet
    df_data = []
    for row in sales_data:
        date, value = row[0], row[1]
        df_data.append({
            "ds": pd.Timestamp(date),
            "y": float(value) if value else 0
        })

    df = pd.DataFrame(df_data).sort_values("ds")

    # Train Prophet model
    try:
        model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
        model.fit(df)

        # Generate forecast
        future = model.make_future_dataframe(periods=forecast_days)
        forecast = model.predict(future)

        # Get only future forecasts
        future_forecast = forecast[forecast["ds"] > df["ds"].max()].copy()

        # Calculate accuracy metrics on historical data
        historical_forecast = forecast[forecast["ds"] <= df["ds"].max()].copy()
        merge_data = df.merge(historical_forecast[["ds", "yhat"]], on="ds", how="inner")
        mae = calculate_mae(merge_data["yhat"].values, merge_data["y"].values)
        mape = calculate_mape(merge_data["yhat"].values, merge_data["y"].values)

        # Store forecasts in database
        for _, row in future_forecast.iterrows():
            forecast_record = Forecast(
                outlet_id=outlet_id,
                product_id=product_id,
                forecast_type="revenue" if not product_id else "demand",
                model_used="Prophet",
                forecast_date=row["ds"].date(),
                forecast_value=float(row["yhat"]) if row["yhat"] > 0 else 0,
                lower_bound=float(row["yhat_lower"]) if row["yhat_lower"] > 0 else 0,
                upper_bound=float(row["yhat_upper"]) if row["yhat_upper"] > 0 else 0,
                generated_at=datetime.now()
            )
            db.add(forecast_record)

        db.commit()

        # Prepare response
        forecast_items = [
            {
                "date": str(row["ds"].date()),
                "predicted_value": max(float(row["yhat"]), 0),
                "confidence_lower": max(float(row["yhat_lower"]), 0),
                "confidence_upper": float(row["yhat_upper"])
            }
            for _, row in future_forecast.iterrows()
        ]

        return {
            "outlet_id": outlet_id,
            "product_id": product_id,
            "forecast_days": forecast_days,
            "from_cache": False,
            "dates": [f["date"] for f in forecast_items],
            "predicted_values": [f["predicted_value"] for f in forecast_items],
            "confidence_lower": [f["confidence_lower"] for f in forecast_items],
            "confidence_upper": [f["confidence_upper"] for f in forecast_items],
            "model_accuracy_metrics": {
                "mae": round(mae, 2),
                "mape": round(mape, 2)
            },
            "factors_impact": {
                "holiday_impact_pct": 0.0,
                "weekend_impact_pct": 0.0
            }
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecasting error: {str(e)}"
        )


@router.get("/inventory")
async def forecast_inventory_reorder(
    outlet_id: int = Query(...),
    product_id: int = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Forecast when a product will reach reorder level based on sales velocity.
    Returns: days_until_reorder, suggested_order_date, suggested_order_quantity
    """
    if not OutletDataAccess.can_access_outlet(outlet_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this outlet"
        )

    # Get product and current inventory
    result = await db.execute(select(Product).where(Product.id == product_id))

    cache_query = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await db.execute(select(Inventory).where(Inventory.outlet_id == outlet_id,
        Inventory.product_id == product_id))

    inventory = result.scalar_one_or_none()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory record not found")

    current_stock = inventory.current_stock
    reorder_point = product.reorder_point

    # Calculate average daily sales (last 30 days)
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    sales_result = db.query(
        func.sum(SaleTransaction.quantity).label("total_qty")
    ).filter(
        SaleTransaction.outlet_id == outlet_id,
        SaleTransaction.product_id == product_id,
        func.date(SaleTransaction.transaction_at) >= thirty_days_ago
    ).first()

    total_30day_sales = sales_result[0] or 0
    avg_daily_sales = total_30day_sales / 30 if total_30day_sales > 0 else 0.1

    # Calculate days until reorder point
    stock_above_reorder = current_stock - reorder_point
    days_until_reorder = int(stock_above_reorder / avg_daily_sales) if avg_daily_sales > 0 else 999

    # Suggested order date
    suggested_order_date = datetime.now().date() + timedelta(days=days_until_reorder)

    # Suggested order quantity: 30-day avg * 1.5 safety factor
    suggested_qty = int(total_30day_sales * 1.5)

    return {
        "product_id": product_id,
        "product_name": product.name,
        "outlet_id": outlet_id,
        "current_stock": current_stock,
        "reorder_point": reorder_point,
        "avg_daily_sales": round(avg_daily_sales, 2),
        "days_until_reorder": max(days_until_reorder, 0),
        "suggested_order_date": str(suggested_order_date),
        "suggested_order_quantity": suggested_qty,
        "estimated_cost": round(suggested_qty * product.cost_price, 2)
    }


@router.get("/factors-analysis")
async def analyze_external_factors(
    outlet_id: int = Query(...),
    period_days: int = Query(90, ge=30, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Analyze historical correlation between external factors and sales.
    Returns which factors (holidays, weekends) had strongest impact.
    """
    if not OutletDataAccess.can_access_outlet(outlet_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this outlet"
        )

    start_date = datetime.now().date() - timedelta(days=period_days)
    end_date = datetime.now().date()

    # Get daily sales data
    daily_sales = db.query(
        func.date(SaleTransaction.transaction_at).label("date"),
        func.sum(SaleTransaction.total_amount).label("revenue"),
        func.sum(SaleTransaction.quantity).label("quantity"),
        func.count(SaleTransaction.id).label("transactions")
    ).filter(
        SaleTransaction.outlet_id == outlet_id,
        func.date(SaleTransaction.transaction_at) >= start_date,
        func.date(SaleTransaction.transaction_at) <= end_date
    ).group_by(func.date(SaleTransaction.transaction_at)))
    product = result.scalars().all()
    if not daily_sales:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No sales data available for analysis"
        )

    # Analyze weekday vs weekend
    weekday_revenue = []
    weekend_revenue = []

    for date, revenue, qty, trans in daily_sales:
        if date.weekday() < 5:  # Monday=0, Friday=4
            weekday_revenue.append(float(revenue) if revenue else 0)
        else:
            weekend_revenue.append(float(revenue) if revenue else 0)

    avg_weekday = np.mean(weekday_revenue) if weekday_revenue else 0
    avg_weekend = np.mean(weekend_revenue) if weekend_revenue else 0
    weekend_impact_pct = ((avg_weekend - avg_weekday) / avg_weekday * 100) if avg_weekday > 0 else 0

    # Simple holiday impact (approximated: peaks in data)
    revenues = [float(row[1]) if row[1] else 0 for row in daily_sales]
    mean_revenue = np.mean(revenues)
    std_revenue = np.std(revenues)

    peak_days = sum(1 for r in revenues if r > mean_revenue + std_revenue)
    holiday_impact_pct = (peak_days / len(revenues) * 100) if revenues else 0

    return {
        "outlet_id": outlet_id,
        "analysis_period_days": period_days,
        "factors": {
            "weekend_impact": {
                "description": "Sales difference between weekends and weekdays",
                "impact_pct": round(weekend_impact_pct, 2),
                "avg_weekday_revenue": round(avg_weekday, 2),
                "avg_weekend_revenue": round(avg_weekend, 2)
            },
            "holiday_impact": {
                "description": "Percentage of days with above-average sales",
                "impact_pct": round(holiday_impact_pct, 2),
                "peak_days_count": peak_days,
                "analysis_days": len(revenues)
            }
        },
        "summary": {
            "strongest_factor": "weekend" if abs(weekend_impact_pct) > abs(holiday_impact_pct) else "holidays",
            "total_impact_range": f"{round(min(weekend_impact_pct, holiday_impact_pct), 2)}% to {round(max(weekend_impact_pct, holiday_impact_pct), 2)}%"
        }
    }


def calculate_mae(predicted, actual):
    """Calculate Mean Absolute Error"""
    if not predicted or not actual or len(predicted) != len(actual):
        return 0
    return np.mean(np.abs(np.array(predicted) - np.array(actual)))


def calculate_mape(predicted, actual):
    """Calculate Mean Absolute Percentage Error"""
    if not predicted or not actual or len(predicted) != len(actual):
        return 0
    predicted = np.array(predicted)
    actual = np.array(actual)
    # Avoid division by zero
    mask = actual != 0
    if not np.any(mask):
        return 0
    return np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100
