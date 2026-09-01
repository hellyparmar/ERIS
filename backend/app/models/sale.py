"""
sale.py - Sale and SaleItem Models
MSc Data Science Project - Enterprise Retail Intelligence System

Covers POS transactions with itemised lines, tax, discounts, and payment tracking.
"""

import enum
from sqlalchemy import (
    Column, String, ForeignKey,
    Integer, DateTime, DECIMAL
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


# ── Enumerations ──────────────────────────────────────────────────────────────

class SalePaymentStatus(enum.Enum):
    PAID     = "paid"
    PARTIAL  = "partial"
    PENDING  = "pending"
    REFUNDED = "refunded"
    VOID     = "void"


class PaymentMethod(enum.Enum):
    CASH    = "cash"
    CARD    = "card"
    UPI     = "upi"
    NEFT    = "neft"
    WALLET  = "wallet"


class SaleChannel(enum.Enum):
    POS      = "pos"
    ONLINE   = "online"
    PHONE    = "phone"
    MANUAL   = "manual"


# ── Sale ──────────────────────────────────────────────────────────────────────



class Refund(Base):
    """
    Records returns and refunds for sold items.
    """
    __tablename__ = "refunds"

    id           = Column(Integer, primary_key=True, index=True)
    sale_id      = Column(Integer, ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True)
    sale_item_id = Column(Integer, ForeignKey("sale_items.id", ondelete="RESTRICT"), index=True)
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    quantity_returned = Column(Integer, nullable=False)
    refund_amount     = Column(DECIMAL(12, 2), nullable=False)
    reason            = Column(String(255))
    refund_method     = Column(String(50), default=PaymentMethod.CASH.value)
    reference         = Column(String(150))

    created_at   = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    sale      = relationship("Sale")
    sale_item = relationship("SaleItem")
    processor = relationship("User", foreign_keys=[processed_by])

    def __repr__(self):
        return f"<Refund sale={self.sale_id} ₹{self.refund_amount}>"
