"""
Forecasting API Router - SIMPLIFIED
Uses simple 30-day moving average for demand forecasting.
No Prophet, ARIMA, LSTM, or ensemble models - just works.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from app.api.db import get_db
from app.api.auth.dependencies import get_current_user
from app.api.services.simple_forecasting import SimpleForecastingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/forecasting", tags=["Forecasting"])


# ============================================================
# PYDANTIC MODELS
# ============================================================

class SimpleForecastRequest(BaseModel):
    store_id: int = Field(default=1, description="Store ID")
    product_id: Optional[int] = Field(None, description="Product ID (None = all products)")
    days_to_forecast: int = Field(30, ge=7, le=90, description="Days to forecast")


# ============================================================
# FORECASTING ENDPOINTS - SIMPLIFIED
# ============================================================

@router.post("/predict")
async def generate_forecast(
    request: SimpleForecastRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate 30-day demand forecast using simple moving average.
    Much simpler than Prophet/ARIMA/LSTM ensemble, but actually reliable.
    """
    try:
        service = SimpleForecastingService(db)
        result = service.forecast_daily_sales(
            store_id=request.store_id,
            product_id=request.product_id,
            days_to_forecast=request.days_to_forecast
        )
        return result
    except Exception as e:
        logger.error(f"Forecasting error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-product")
async def forecast_by_product(
    store_id: int = Query(1),
    days_to_forecast: int = Query(30, ge=7, le=90),
    top_n: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate forecasts for top N products by sales volume.
    """
    try:
        service = SimpleForecastingService(db)
        result = service.forecast_by_product(
            store_id=store_id,
            days_to_forecast=days_to_forecast,
            top_n=top_n
        )
        return result
    except Exception as e:
        logger.error(f"Product forecast error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
