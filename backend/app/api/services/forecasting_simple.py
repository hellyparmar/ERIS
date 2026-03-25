"""
Forecasting Service - SIMPLIFIED
Uses simple 30-day moving average instead of ARIMA/Prophet/XGBoost
"""

from sqlalchemy.orm import Session
from app.api.services.simple_forecasting import SimpleForecastingService
from typing import Optional, Dict, Any


def build_forecast(
    db: Session,
    store_id: Optional[int] = None,
    horizon: int = 30
) -> Dict[str, Any]:
    """
    Build sales forecast using simple 30-day moving average.
    
    This replaces the complex ARIMA implementation with something
    that actually works and is maintainable.
    """
    service = SimpleForecastingService(db)
    return service.forecast_daily_sales(
        store_id=store_id or 1,
        days_to_forecast=horizon
    )


def build_forecast_by_product(
    db: Session,
    store_id: int,
    horizon: int = 30,
    top_n: int = 10
) -> Dict[str, Any]:
    """
    Forecast for top N products
    """
    service = SimpleForecastingService(db)
    return service.forecast_by_product(
        store_id=store_id,
        days_to_forecast=horizon,
        top_n=top_n
    )
