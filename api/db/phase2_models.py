"""
Phase 2 Database Models for Invoice, Khata, and GST Management

Extends the Phase 1 database with invoice and credit management capabilities
"""

from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from .base import Base


# ==================== Supporting Models ====================

class Business(Base):
    """Business model for testing"""
    __tablename__ = "businesses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    gst_number = Column(String(15), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    invoices = relationship("Invoice", back_populates="business")
    customer_credits = relationship("CustomerCredit", back_populates="business")
    gst_config = relationship("GSTConfiguration", back_populates="business")


class Customer(Base):
    """Customer model for testing"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    gst_number = Column(String(15), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    invoices = relationship("Invoice", back_populates="customer")
    credit_account = relationship("CustomerCredit", back_populates="customer", uselist=False)


class Product(Base):
    """Product model for testing"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    hsn_code = Column(String(8), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    invoice_items = relationship("InvoiceLineItem", back_populates="product")


# ==================== Invoice Models ====================

class Invoice(Base):
    """Invoice model for GST-compliant invoicing"""
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # Invoice numbering
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    invoice_date = Column(Date, nullable=False)
    
    # Customer details
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer_name = Column(String(255), nullable=False)
    customer_gst_number = Column(String(15), nullable=True)
    
    # Address details
    billing_address = Column(Text, nullable=False)
    shipping_address = Column(Text, nullable=True)
    
    # Amount details
    subtotal = Column(Numeric(12, 2), nullable=False)  # Before tax
    cgst_amount = Column(Numeric(12, 2), default=0)  # Central GST
    sgst_amount = Column(Numeric(12, 2), default=0)  # State GST
    igst_amount = Column(Numeric(12, 2), default=0)  # Integrated GST
    total_tax = Column(Numeric(12, 2), nullable=False)
    grand_total = Column(Numeric(12, 2), nullable=False)  # After tax
    
    # Discount
    discount_amount = Column(Numeric(12, 2), default=0)
    discount_percentage = Column(Numeric(5, 2), default=0)
    
    # Additional charges
    shipping_charges = Column(Numeric(12, 2), default=0)
    other_charges = Column(Numeric(12, 2), default=0)
    
    # Invoice details
    due_date = Column(Date, nullable=True)
    payment_terms = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Status tracking
    status = Column(String(20), default="DRAFT")  # DRAFT, SENT, PAID, OVERDUE, CANCELLED
    payment_status = Column(String(20), default="UNPAID")  # UNPAID, PARTIAL, PAID
    
    # Delivery status
    whatsapp_sent = Column(Boolean, default=False)
    whatsapp_sent_at = Column(DateTime, nullable=True)
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)
    
    # Tax classification
    is_inter_state = Column(Boolean, default=False)
    igst_category = Column(String(20), nullable=True)  # 0%, 5%, 12%, 18%, 28%
    
    # E-Invoice fields (for India compliance)
    e_invoice_irn = Column(String(64), nullable=True)  # IRN from e-invoice portal
    e_invoice_acked_date = Column(DateTime, nullable=True)
    e_invoice_qr_code = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    business = relationship("Business", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("InvoicePayment", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLineItem(Base):
    """Line items in an invoice"""
    __tablename__ = "invoice_line_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    
    # Product details
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(255), nullable=False)
    hsn_code = Column(String(10), nullable=False)
    
    # Description
    description = Column(Text, nullable=True)
    
    # Quantity and rate
    quantity = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(20), default="PCS")
    unit_rate = Column(Numeric(12, 2), nullable=False)
    
    # Amount before tax
    line_amount = Column(Numeric(12, 2), nullable=False)
    
    # Tax details
    tax_rate = Column(Numeric(5, 2), nullable=False)  # 0, 5, 12, 18, 28
    cgst_amount = Column(Numeric(12, 2), default=0)
    sgst_amount = Column(Numeric(12, 2), default=0)
    igst_amount = Column(Numeric(12, 2), default=0)
    
    # Final amount after tax
    line_total = Column(Numeric(12, 2), nullable=False)
    
    # Discount on line item
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")
    product = relationship("Product", back_populates="invoice_items")


class InvoicePayment(Base):
    """Payment records for invoices"""
    __tablename__ = "invoice_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    
    # Payment details
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)  # CASH, CHEQUE, BANK, UPI, etc.
    
    # Reference
    reference_number = Column(String(100), nullable=True)  # Check no, transaction ID, etc.
    
    # Notes
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="payments")


class CustomerCredit(Base):
    """Khata/Credit management for customers"""
    __tablename__ = "customer_credit"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), unique=True, nullable=False)
    
    # Credit limit
    credit_limit = Column(Numeric(12, 2), nullable=False, default=0)
    current_balance = Column(Numeric(12, 2), nullable=False, default=0)  # Amount owed
    
    # Credit scoring
    credit_score = Column(Integer, default=100)  # 0-100 scale
    credit_rating = Column(String(20), default="GOOD")  # EXCELLENT, GOOD, FAIR, POOR
    
    # Payment tracking
    total_transactions = Column(Integer, default=0)
    on_time_payments = Column(Integer, default=0)
    late_payments = Column(Integer, default=0)
    missed_payments = Column(Integer, default=0)
    
    # Dates
    last_payment_date = Column(Date, nullable=True)
    last_transaction_date = Column(Date, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)  # Block further credit
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    business = relationship("Business", back_populates="customer_credits")
    customer = relationship("Customer", back_populates="credit_account")
    transactions = relationship("CreditTransaction", back_populates="credit_account", cascade="all, delete-orphan")
    reminders = relationship("CreditReminder", back_populates="credit_account", cascade="all, delete-orphan")


class CreditTransaction(Base):
    """Individual credit transaction records"""
    __tablename__ = "credit_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    credit_account_id = Column(Integer, ForeignKey("customer_credit.id"), nullable=False)
    
    # Transaction type
    transaction_type = Column(String(20), nullable=False)  # DEBIT (sale), CREDIT (payment)
    
    # Reference
    reference_id = Column(String(100), nullable=True)  # Invoice ID, Payment ID
    reference_type = Column(String(50), nullable=True)  # INVOICE, PAYMENT, ADJUSTMENT
    
    # Amount
    amount = Column(Numeric(12, 2), nullable=False)
    balance_after = Column(Numeric(12, 2), nullable=False)  # Running balance
    
    # Description
    description = Column(Text, nullable=True)
    
    # Due date (for DEBIT transactions)
    due_date = Column(Date, nullable=True)
    payment_due = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    credit_account = relationship("CustomerCredit", back_populates="transactions")


class CreditReminder(Base):
    """Payment reminder records"""
    __tablename__ = "credit_reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    credit_account_id = Column(Integer, ForeignKey("customer_credit.id"), nullable=False)
    
    # Outstanding amount
    outstanding_amount = Column(Numeric(12, 2), nullable=False)
    days_overdue = Column(Integer, default=0)
    
    # Reminder details
    reminder_type = Column(String(20), nullable=False)  # SMS, EMAIL, WHATSAPP
    reminder_number = Column(Integer, default=1)  # 1st, 2nd, 3rd reminder
    
    # Status
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    
    # Response
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # Message details
    message_id = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    credit_account = relationship("CustomerCredit", back_populates="reminders")


class GSTConfiguration(Base):
    """GST configuration for business"""
    __tablename__ = "gst_configuration"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), unique=True, nullable=False)
    
    # GST registration details
    gst_number = Column(String(15), nullable=False)  # GSTIN
    business_name = Column(String(255), nullable=False)
    
    # Address
    business_address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    
    # Financial year
    financial_year_start = Column(Date, nullable=False)
    financial_year_end = Column(Date, nullable=False)
    
    # Configuration flags
    is_registered = Column(Boolean, default=True)
    is_composition = Column(Boolean, default=False)  # Composition scheme
    
    # Default tax rates for this business
    default_tax_rate = Column(Numeric(5, 2), default=18)  # 0, 5, 12, 18, 28
    
    # E-Invoice settings
    enable_e_invoice = Column(Boolean, default=True)
    e_invoice_username = Column(String(255), nullable=True)
    e_invoice_password = Column(String(255), nullable=True)
    
    # Returns configuration
    returns_filing_date = Column(Date, nullable=True)  # GSTR-1 due date
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    business = relationship("Business", back_populates="gst_config")


# Extend existing tables with new fields (in migrations)
# products: hsn_code, gst_category, tax_rate
# customers: credit_limit, credit_score
# businesses: gst_number, registered_address
