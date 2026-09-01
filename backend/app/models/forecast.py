"""
Forecast Models - Time-series forecasting and prediction storage
"""

from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, Enum, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
import enum
import uuid
from sqlalchemy.types import Uuid
from datetime import datetime

class ForecastType(str, enum.Enum):
    revenue = "revenue"
    demand = "demand"

class Forecast(Base):
    __tablename__ = "forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    outlet_id: Mapped[int] = mapped_column(Integer, ForeignKey("outlets.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("products.id"), nullable=True)
    forecast_type: Mapped[ForecastType] = mapped_column(Enum(ForecastType), nullable=False)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    forecast_date: Mapped[Date] = mapped_column(Date, nullable=False)
    forecast_value: Mapped[float] = mapped_column(Float, nullable=False)
    lower_bound: Mapped[float] = mapped_column(Float, nullable=True)
    upper_bound: Mapped[float] = mapped_column(Float, nullable=True)
    actual_value: Mapped[float] = mapped_column(Float, nullable=True)
    generated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class ForecastResult(Base):
    """
    Stores forecast evaluation results and metrics.
    
    Used to track forecast accuracy (MAPE, RMSE, MAE) over time,
    enabling model comparison and performance monitoring.
    """
    __tablename__ = "forecast_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    outlet_id: Mapped[int] = mapped_column(Integer, ForeignKey("outlets.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("products.id"), nullable=True)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "prophet", "lstm", "ensemble"
    forecast_json: Mapped[str] = mapped_column(Text, nullable=True)  # JSON serialized forecast data
    mape: Mapped[float] = mapped_column(Float, nullable=True)  # Mean Absolute Percentage Error
    rmse: Mapped[float] = mapped_column(Float, nullable=True)  # Root Mean Squared Error
    mae: Mapped[float] = mapped_column(Float, nullable=True)  # Mean Absolute Error
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)