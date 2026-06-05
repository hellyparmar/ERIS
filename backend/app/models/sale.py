"""
sale.py - Sale and SaleItem Models
MSc Data Science Project - Enterprise Retail Intelligence System

Covers POS transactions with itemised lines, tax, discounts, and payment tracking.
"""

import enum
import uuid
from sqlalchemy import (
    Column, String, Boolean, ForeignKey,
    Integer, DateTime, DECIMAL, Text, Index, UniqueConstraint, text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Uuid, JSON

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
    CREDIT  = "credit"   # Khata / buy now pay later


class SaleChannel(enum.Enum):
    POS      = "pos"
    ONLINE   = "online"
    PHONE    = "phone"
    MANUAL   = "manual"


# ── Sale ──────────────────────────────────────────────────────────────────────

class Sale(Base):
    """
    A retail sales transaction.
    Linked to a store (outlet), optionally to a customer, and to line items.
    """
    __tablename__ = "sales"

    id              = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    transaction_id  = Column(String(100), unique=True, index=True)     # human-readable receipt no.

    # Tenant scope
    organization_id = Column(Uuid(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    store_id        = Column(Uuid(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)

    # Parties
    customer_id     = Column(Uuid(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), index=True)
    cashier_id      = Column(Uuid(as_uuid=True), ForeignKey("users.id",     ondelete="SET NULL"), index=True)

    # Financials (all in INR, 2dp)
    subtotal        = Column(DECIMAL(12, 2), nullable=False, default=0)
    discount        = Column(DECIMAL(12, 2), default=0)
    tax_amount      = Column(DECIMAL(12, 2), default=0)     # total GST collected
    total_amount    = Column(DECIMAL(12, 2), nullable=False)
    amount_paid     = Column(DECIMAL(12, 2), default=0)
    change_due      = Column(DECIMAL(12, 2), default=0)

    # Payment
    payment_method  = Column(String(50), default=PaymentMethod.CASH.value)
    payment_status  = Column(String(20), default=SalePaymentStatus.PAID.value, index=True)
    payment_reference = Column(String(150))                 # UPI ref, card auth code…

    # Channel / Source
    channel         = Column(String(30), default=SaleChannel.POS.value)
    notes           = Column(Text)
    invoice_id      = Column(Integer, ForeignKey("invoices.id", ondelete="SET NULL"))

    # Timestamps
    transaction_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), onupdate=func.now())
    voided_at        = Column(DateTime(timezone=True))
    voided_by        = Column(Integer, ForeignKey("users.id"))

    # Relationships
    customer  = relationship("Customer", back_populates="sales",   foreign_keys=[customer_id])
    cashier   = relationship("User",     foreign_keys=[cashier_id])
    items     = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    invoice   = relationship("Invoice",  back_populates="sales",   foreign_keys=[invoice_id])

    __table_args__ = (
        Index("idx_sale_org_date",    "organization_id", "transaction_date"),
        Index("idx_sale_store_date",  "store_id",        "transaction_date"),
        Index("idx_sale_customer",    "customer_id"),
        Index("idx_sale_payment",     "payment_status"),
    )

    @property
    def is_void(self) -> bool:
        return self.payment_status == SalePaymentStatus.VOID.value

    def __repr__(self):
        return f"<Sale {self.transaction_id} ₹{self.total_amount}>"


# ── Sale Item ─────────────────────────────────────────────────────────────────

class SaleItem(Base):
    """
    Individual line item within a sale.
    Captures snapshot prices at the time of the transaction.
    """
    __tablename__ = "sale_items"

    id          = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    sale_id     = Column(Uuid(as_uuid=True), ForeignKey("sales.id",    ondelete="CASCADE"), nullable=False, index=True)
    product_id  = Column(Uuid(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)

    # Snapshot pricing (frozen at time of sale)
    product_name = Column(String(255))          # denormalised for reporting
    product_sku  = Column(String(100))
    unit_price   = Column(DECIMAL(12, 2), nullable=False)
    cost_price   = Column(DECIMAL(12, 2))       # COGS snapshot

    quantity     = Column(Integer, nullable=False)
    discount     = Column(DECIMAL(12, 2), default=0)
    tax_rate     = Column(DECIMAL(5,  2), default=0)     # GST % applied
    tax_amount   = Column(DECIMAL(12, 2), default=0)
    line_total   = Column(DECIMAL(12, 2), nullable=False) # (unit_price - discount) * qty + tax_amount

    # Relationships
    sale    = relationship("Sale",    back_populates="items")
    product = relationship("Product", back_populates="sale_items")

    __table_args__ = (
        Index("idx_sale_item_product", "product_id"),
    )

    @property
    def gross_profit(self) -> float:
        if self.cost_price:
            return round((float(self.unit_price) - float(self.cost_price)) * self.quantity, 2)
        return 0.0

    def __repr__(self):
        return f"<SaleItem sale={self.sale_id} product={self.product_id} qty={self.quantity}>"


# ── Refund ────────────────────────────────────────────────────────────────────

class Refund(Base):
    """
    Records returns and refunds for sold items.
    """
    __tablename__ = "refunds"

    id           = Column(Integer, primary_key=True, index=True)
    sale_id      = Column(Integer, ForeignKey("sales.id",      ondelete="RESTRICT"), nullable=False, index=True)
    sale_item_id = Column(Integer, ForeignKey("sale_items.id", ondelete="RESTRICT"), index=True)
    processed_by = Column(Integer, ForeignKey("users.id"),     nullable=False)

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
