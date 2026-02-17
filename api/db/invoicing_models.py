"""
Invoice & Billing Models
Comprehensive invoicing system with GST, TDS, and payment tracking
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from api.db import Base


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CHEQUE = "cheque"
    UPI = "upi"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"
    WALLET = "wallet"
    CREDIT = "credit"


class Invoice(Base):
    """Main invoice table"""
    __tablename__ = "invoices"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, index=True)
    
    # Customer info
    customer_id = Column(Integer, index=True)  # Reference to customers table (if exists)
    customer_name = Column(String)
    customer_email = Column(String)
    customer_phone = Column(String)
    
    # Dates
    invoice_date = Column(DateTime, default=datetime.now, index=True)
    due_date = Column(DateTime)
    payment_date = Column(DateTime, nullable=True)
    
    # Amounts
    subtotal = Column(Float, default=0)  # Before tax
    gst_amount = Column(Float, default=0)
    gst_rate = Column(Float, default=18.0)  # GST percentage
    tds_amount = Column(Float, default=0)
    tds_rate = Column(Float, default=0)  # TDS percentage
    total_amount = Column(Float, default=0)  # After tax
    
    # Payment tracking
    amount_paid = Column(Float, default=0)
    balance_amount = Column(Float, default=0)
    
    # Status
    status = Column(String, default=InvoiceStatus.DRAFT)
    payment_status = Column(String, default="unpaid")  # unpaid, partial, paid
    
    # Details
    description = Column(Text)
    notes = Column(Text)
    terms = Column(Text)
    
    # Reference (optional - sales table may not exist)
    sale_id = Column(Integer, nullable=True)  # ForeignKey to sales.id if exists
    reference_number = Column(String, nullable=True)
    
    # Metadata
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    taxes = relationship("InvoiceTax", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLineItem(Base):
    """Invoice line items"""
    __tablename__ = "invoice_line_items"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), index=True)
    
    # Product info
    product_id = Column(Integer, nullable=True)  # Optional reference to products.id
    product_name = Column(String)
    product_sku = Column(String)
    
    # Line details
    description = Column(String)
    quantity = Column(Float)
    unit_price = Column(Float)
    line_total = Column(Float)
    
    # Tax on line item
    gst_rate = Column(Float, default=18.0)
    gst_amount = Column(Float, default=0)
    line_total_with_tax = Column(Float)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")


class Payment(Base):
    """Payment tracking"""
    __tablename__ = "payments"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), index=True)
    
    # Payment details
    payment_date = Column(DateTime, default=datetime.now)
    amount_paid = Column(Float)
    payment_method = Column(String)  # cash, cheque, upi, etc.
    reference_number = Column(String)  # Cheque number, Transaction ID, etc.
    
    # Bank details (if applicable)
    bank_name = Column(String, nullable=True)
    bank_account = Column(String, nullable=True)
    transaction_id = Column(String, nullable=True)
    
    # Status
    status = Column(String, default="completed")  # pending, completed, failed
    
    # Notes
    notes = Column(Text)
    
    # Metadata
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="payments")


class InvoiceTax(Base):
    """Detailed tax breakdown"""
    __tablename__ = "invoice_taxes"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), index=True)
    
    # Tax details
    tax_name = Column(String)  # SGST, CGST, IGST, TDS, etc.
    tax_rate = Column(Float)
    tax_amount = Column(Float)
    
    # Classification
    tax_type = Column(String)  # gst, tds, cess, etc.
    hsn_code = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="taxes")


class GSTRate(Base):
    """GST rate master"""
    __tablename__ = "gst_rates"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    product_category = Column(String, unique=True, index=True)
    gst_rate = Column(Float)
    hsn_code = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Bill(Base):
    """Bills for purchases/expenses"""
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True)
    bill_number = Column(String, unique=True, index=True)
    
    # Vendor info
    vendor_name = Column(String)
    vendor_email = Column(String)
    vendor_phone = Column(String)
    vendor_gst = Column(String)
    
    # Dates
    bill_date = Column(DateTime, default=datetime.now)
    due_date = Column(DateTime)
    payment_date = Column(DateTime, nullable=True)
    
    # Amounts
    subtotal = Column(Float, default=0)
    gst_amount = Column(Float, default=0)
    gst_rate = Column(Float, default=18.0)
    total_amount = Column(Float, default=0)
    
    # Payment
    amount_paid = Column(Float, default=0)
    balance_amount = Column(Float, default=0)
    status = Column(String, default="unpaid")  # unpaid, partial, paid
    
    # Details
    description = Column(Text)
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)


class CreditNote(Base):
    """Credit notes for returns/adjustments"""
    __tablename__ = "credit_notes"

    id = Column(Integer, primary_key=True, index=True)
    credit_note_number = Column(String, unique=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    
    # Dates
    issue_date = Column(DateTime, default=datetime.now)
    
    # Amount
    amount = Column(Float)
    reason = Column(String)
    description = Column(Text)
    
    # Status
    status = Column(String, default="issued")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now)


class DebitNote(Base):
    """Debit notes for additional charges"""
    __tablename__ = "debit_notes"

    id = Column(Integer, primary_key=True, index=True)
    debit_note_number = Column(String, unique=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    
    # Dates
    issue_date = Column(DateTime, default=datetime.now)
    
    # Amount
    amount = Column(Float)
    reason = Column(String)
    description = Column(Text)
    
    # Status
    status = Column(String, default="issued")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now)
