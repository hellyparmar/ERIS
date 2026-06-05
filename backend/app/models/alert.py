"""
Alert Models
"""

from sqlalchemy import String, Boolean, Text, DateTime, ForeignKey, Enum, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid
from app.models.base import Base
import enum
import uuid

class AlertType(str, enum.Enum):
    low_stock = "low_stock"
    stockout = "stockout"
    expiry_risk = "expiry_risk"
    sales_anomaly = "sales_anomaly"
    forecast_deviation = "forecast_deviation"
    supplier_delay = "supplier_delay"
    gst_reminder = "gst_reminder"

class AlertSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    outlet_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("outlets.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("products.id"), nullable=True)
    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType), nullable=False)
    severity: Mapped[AlertSeverity] = mapped_column(Enum(AlertSeverity), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_by: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    acknowledged_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
