"""
invoicing.py - Invoice Model
MSc Data Science Project - Enterprise Retail Intelligence System

Handles GST invoicing, payment tracking, and billing integration with sales.
"""

import enum
from sqlalchemy import BigInteger, Boolean, Column, DateTime, DECIMAL, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


# ── Enumerations ──────────────────────────────────────────────────────────────


class InvoiceStatus(enum.Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class InvoiceType(enum.Enum):
    TAX_INVOICE = "tax_invoice"
    SIMPLIFIED = "simplified"
    BILL = "bill"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"


# ── Invoice ───────────────────────────────────────────────────────────────────


class Invoice(Base):
    """
    GST-compliant invoice with payment tracking and billing integration.
    Linked to one or more Sales.
    """

    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="SET NULL"), nullable=True, index=True)

    # Tenant & store scope
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    outlet_id = Column(Integer, ForeignKey("outlets.id", ondelete="SET NULL"), index=True)

    # Customer
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), index=True)

    # Billing party
    billed_to_name = Column(String(255))
    billed_to_gstin = Column(String(15))
    billed_to_address = Column(Text)

    # Invoice details
    invoice_type = Column(String(30), default=InvoiceType.TAX_INVOICE.value)
    invoice_date = Column(DateTime(timezone=True), nullable=False, index=True)
    due_date = Column(DateTime(timezone=True))

    # Financials (all in INR, 2dp)
    subtotal = Column(DECIMAL(12, 2), nullable=False, default=0)
    discount = Column(DECIMAL(12, 2), default=0)
    tax_amount = Column(DECIMAL(12, 2), default=0)  # total IGST/SGST/CGST
    total_amount = Column(DECIMAL(12, 2), nullable=False)
    amount_paid = Column(DECIMAL(12, 2), default=0)
    amount_due = Column(DECIMAL(12, 2), default=0)

    # Payment
    payment_status = Column(String(20), default=InvoiceStatus.ISSUED.value, index=True)
    payment_terms = Column(String(100))  # e.g. "Net 30", "Cash on Delivery"
    last_payment_at = Column(DateTime(timezone=True))

    # References
    po_number = Column(String(100))  # Purchase Order ref
    notes = Column(Text)

    # GST Fields (India-specific)
    igst_rate = Column(DECIMAL(5, 2), default=0)
    sgst_rate = Column(DECIMAL(5, 2), default=0)
    cgst_rate = Column(DECIMAL(5, 2), default=0)
    igst_amount = Column(DECIMAL(12, 2), default=0)
    sgst_amount = Column(DECIMAL(12, 2), default=0)
    cgst_amount = Column(DECIMAL(12, 2), default=0)

    # Status
    is_active = Column(Boolean, default=True)
    is_voided = Column(Boolean, default=False)
    voided_at = Column(DateTime(timezone=True))
    voided_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    sent_at = Column(DateTime(timezone=True))

    # Relationships
    organization = relationship("Organization")
    outlet = relationship("Outlet")
    customer = relationship("Customer")
    sale = relationship("Sale", foreign_keys=[sale_id])
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    taxes = relationship("InvoiceTax", back_populates="invoice", cascade="all, delete-orphan")
    voided_by_user = relationship("User", foreign_keys=[voided_by])

    __table_args__ = (
        Index("idx_invoice_org_date", "organization_id", "invoice_date"),
        Index("idx_invoice_store_date", "outlet_id", "invoice_date"),
        Index("idx_invoice_customer", "customer_id"),
        Index("idx_invoice_status", "payment_status"),
        Index("idx_invoice_amount_due", "amount_due"),
    )

    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue (due_date passed and not fully paid)."""
        from datetime import datetime, timezone as tz

        if not self.due_date:
            return False
        return datetime.now(tz.utc) > self.due_date.replace(tzinfo=tz.utc) and self.amount_due > 0

    def __repr__(self):
        return f"<Invoice {self.invoice_number} ₹{self.total_amount}>"


class InvoiceLineItem(Base):
    """A priced and taxed line on an invoice."""

    __tablename__ = "invoice_line_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    product_name = Column(String(300), nullable=False)
    product_sku = Column(String(50))
    description = Column(String(500))
    quantity = Column(DECIMAL(12, 3), nullable=False)
    unit_price = Column(DECIMAL(12, 2), nullable=False)
    line_total = Column(DECIMAL(12, 2), nullable=False)
    gst_rate = Column(DECIMAL(5, 2), nullable=False, default=0)
    gst_amount = Column(DECIMAL(12, 2), nullable=False, default=0)
    line_total_with_tax = Column(DECIMAL(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    invoice = relationship("Invoice", back_populates="line_items")


class Payment(Base):
    """Payment recorded against an invoice and optionally its source sale."""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_id = Column(BigInteger, ForeignKey("sales.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    payment_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    amount_paid = Column(DECIMAL(12, 2), nullable=False)
    payment_method = Column(String(30), nullable=False)
    reference_number = Column(String(100))
    bank_name = Column(String(120))
    bank_account = Column(String(100))
    transaction_id = Column(String(100))
    status = Column(String(20), nullable=False, default="completed")
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    invoice = relationship("Invoice", back_populates="payments")
    sale = relationship("Sale", back_populates="payments")
    customer = relationship("Customer", backref="payments")


class InvoiceTax(Base):
    """Tax component attached to an invoice."""

    __tablename__ = "invoice_taxes"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    tax_name = Column(String(30), nullable=False)
    tax_rate = Column(DECIMAL(5, 2), nullable=False)
    tax_amount = Column(DECIMAL(12, 2), nullable=False)
    tax_type = Column(String(30), nullable=False)
    hsn_code = Column(String(20))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    invoice = relationship("Invoice", back_populates="taxes")
