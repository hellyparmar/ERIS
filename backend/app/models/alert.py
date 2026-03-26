"""
alert.py - Alert Model
MSc Data Science Project - Enterprise Retail Intelligence System

Covers system-generated alerts: low stock, anomaly detection, and forecast warnings.
"""

import enum
from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey,
    DateTime, Text, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Uuid, JSON

from .base import Base


# ── Enumerations ──────────────────────────────────────────────────────────────

class AlertType(enum.Enum):
    LOW_STOCK        = "low_stock"
    OUT_OF_STOCK     = "out_of_stock"
    OVERSTOCK        = "overstock"
    ANOMALY          = "anomaly"
    FORECAST_WARNING = "forecast_warning"
    PAYMENT_OVERDUE  = "payment_overdue"
    SYSTEM           = "system"


class AlertSeverity(enum.Enum):
    CRITICAL = "critical"
    WARNING  = "warning"
    INFO     = "info"


# ── Alert ─────────────────────────────────────────────────────────────────────

class Alert(Base):
    """
    System-generated alert visible in the dashboard notification panel.

    Alerts are created by:
    - Inventory service  → LOW_STOCK / OUT_OF_STOCK
    - ML forecaster      → FORECAST_WARNING
    - Anomaly detector   → ANOMALY
    - Payment service    → PAYMENT_OVERDUE
    """
    __tablename__ = "alerts"

    id              = Column(Integer, primary_key=True, index=True)

    # Tenant scope
    organization_id = Column(Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id        = Column(Uuid(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), index=True)

    # Alert metadata
    alert_type      = Column(String(50), nullable=False, index=True)
    severity        = Column(String(20), default=AlertSeverity.WARNING.value, index=True)
    title           = Column(String(255), nullable=False)
    message         = Column(Text, nullable=False)

    # Optional entity references
    product_id      = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), index=True)
    sale_id         = Column(Integer, ForeignKey("sales.id",    ondelete="SET NULL"))
    extra_data      = Column(JSON, default=dict)      # e.g. {"predicted_stockout": "2026-04-01"}

    # Status
    is_read         = Column(Boolean, default=False, index=True)
    is_resolved     = Column(Boolean, default=False, index=True)

    read_by         = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    read_at         = Column(DateTime(timezone=True))
    resolved_by     = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    resolved_at     = Column(DateTime(timezone=True))
    resolution_note = Column(Text)

    # Auto-expiry
    expires_at      = Column(DateTime(timezone=True))

    # Timestamps
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    product         = relationship("Product", back_populates="alerts",  foreign_keys=[product_id])
    store           = relationship("Store",   back_populates="alerts",  foreign_keys=[store_id])
    reader          = relationship("User",    foreign_keys=[read_by])
    resolver        = relationship("User",    foreign_keys=[resolved_by])

    __table_args__ = (
        Index("idx_alert_org_unread",      "organization_id", "is_read"),
        Index("idx_alert_org_type",        "organization_id", "alert_type"),
        Index("idx_alert_store_type",      "store_id",        "alert_type"),
        Index("idx_alert_severity_active", "severity",        "is_resolved"),
    )

    def __repr__(self):
        return f"<Alert [{self.alert_type}] {self.title}>"
