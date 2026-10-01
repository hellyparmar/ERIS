"""
Forecast Models - Time-series forecasting and prediction storage
"""

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
from datetime import datetime


class ForecastResult(Base):
    """
    Stores generated forecasts and evaluation metrics.

    Used to track forecast accuracy (MAPE, RMSE, MAE) over time,
    enabling model comparison and performance monitoring.
    """

    __tablename__ = "forecast_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    outlet_id: Mapped[int] = mapped_column(Integer, ForeignKey("outlets.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("products.id"), nullable=True)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "prophet", "xgboost", "ensemble"
    forecast_json: Mapped[str] = mapped_column(Text, nullable=True)  # JSON serialized forecast data
    mape: Mapped[float] = mapped_column(Float, nullable=True)  # Mean Absolute Percentage Error
    rmse: Mapped[float] = mapped_column(Float, nullable=True)  # Root Mean Squared Error
    mae: Mapped[float] = mapped_column(Float, nullable=True)  # Mean Absolute Error
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )
