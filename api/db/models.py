"""
SQLAlchemy ORM Models for R-DIOS v5.0
Complete database schema with Transaction Engine, Communication Hub, and Community Commerce
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum, Numeric, DECIMAL, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base
import enum

# ==================== ENUMERATIONS ====================

class AlertSeverity(enum.Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class PaymentStatus(enum.Enum):
    """Invoice payment status"""
    PAID = "paid"
    PARTIAL = "partial"
    PENDING = "pending"
    OVERDUE = "overdue"

class MessageChannel(enum.Enum):
    """Communication channels"""
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"

class ListingType(enum.Enum):
    """Community listing types"""
    STOCK_SWAP = "stock_swap"
    BULK_BUY_REQUEST = "bulk_buy_request"

# ==================== EXISTING TABLES (UPDATED) ====================
# We re-export it here so other modules can import it from api.db.models
# Product, Customer, Supplier models are imported from multitenant_models

from api.db.multitenant_models import User, UserRole, Product, Customer, Supplier, Invoice, PaymentStatus, Inventory, PurchaseOrder, PurchaseOrderItem

class Sale(Base):
    """Sales transactions with payment tracking"""
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(100), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    store_id = Column(Integer, index=True)
    
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    discount = Column(DECIMAL(12, 2), default=0.0)
    tax = Column(DECIMAL(12, 2), default=0.0)
    total_amount = Column(DECIMAL(12, 2), nullable=False)
    
    payment_method = Column(String(50))
    
    # Payment Status Tracking (NEW)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PAID, index=True)
    installments = Column(Integer, default=1)
    
    source = Column(String(50), default="manual")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="sales")
    invoice = relationship("Invoice", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

class SaleItem(Base):
    """Line items for sales transactions"""
    __tablename__ = "sale_items"
    
    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(12, 2), nullable=False)
    line_total = Column(DECIMAL(12, 2), nullable=False)
    
    # Relationships
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")

# Inventory moved to multitenant_models.py

class Alert(Base):
    """System alerts and notifications"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    severity = Column(Enum(AlertSeverity), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(50))
    related_product_id = Column(Integer, ForeignKey("products.id"))
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"))
    acknowledged_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True))
    
    # Relationships
    related_product = relationship("Product", back_populates="alerts")
    acknowledged_by_user = relationship("User") # back_populates removed for schema simplicity during load

class SyncLog(Base):
    """ERP sync history"""
    __tablename__ = "sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)
    sync_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    records_imported = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    initiated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    triggered_by = relationship("User") # back_populates removed for load simplicity

# ==================== NEW TABLES (Phase 1) ====================

# Invoice moved to multitenant_models.py

class InvoicePayment(Base):
    """Partial payment tracking for Khata system"""
    __tablename__ = "invoice_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False, index=True)
    
    payment_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    amount_paid = Column(DECIMAL(12, 2), nullable=False)
    payment_method = Column(String(50))  # cash, card, upi, neft
    reference_number = Column(String(100))
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="payments")

class CustomerCredit(Base):
    """Customer credit/Khata balances"""
    __tablename__ = "customer_credits"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), unique=True, nullable=False, index=True)
    
    credit_limit = Column(DECIMAL(12, 2), default=0.0)
    current_balance = Column(DECIMAL(12, 2), default=0.0)  # How much they owe
    last_payment_date = Column(DateTime(timezone=True))
    credit_score = Column(Integer)  # 0-100
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships — use class directly to avoid ambiguity with models_v6.Customer
    customer = relationship(Customer, back_populates="credit_account", foreign_keys=[customer_id])

class Message(Base):
    """Unified communication hub"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String(50), index=True)  # Group related messages
    
    # Polymorphic sender/recipient
    sender_type = Column(String(20), nullable=False)  # customer, supplier, staff, system
    sender_id = Column(Integer, nullable=False)
    recipient_type = Column(String(20), nullable=False)
    recipient_id = Column(Integer, nullable=False)
    
    # Contextual linking
    related_entity_type = Column(String(20))  # invoice, order, product
    related_entity_id = Column(Integer)
    
    channel = Column(Enum(MessageChannel), nullable=False)
    subject = Column(String(255))
    body = Column(Text, nullable=False)
    attachments = Column(JSON)  # [{url, type, name}]
    
    status = Column(String(20), default="sent")  # sent, delivered, read, replied
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    read_at = Column(DateTime(timezone=True))

class CommunityListing(Base):
    """Stock swapping and bulk buying marketplace"""
    __tablename__ = "community_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    listing_type = Column(Enum(ListingType), nullable=False, index=True)
    retailer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Stock swap fields
    quantity_available = Column(Integer)
    price_per_unit = Column(DECIMAL(12, 2))
    reason = Column(String(50))  # dead_stock, overstock, seasonal
    
    # Bulk buy fields
    quantity_needed = Column(Integer)
    target_price = Column(DECIMAL(12, 2))
    
    location = Column(String(255))
    expires_at = Column(DateTime(timezone=True))
    status = Column(String(20), default="active", index=True)  # active, matched, completed, expired
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    retailer = relationship("User")
    product = relationship("Product", back_populates="community_listings")

class BulkBuyGroup(Base):
    """Aggregated demand for bulk ordering"""
    __tablename__ = "bulk_buy_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    target_quantity = Column(Integer, nullable=False)
    current_quantity = Column(Integer, default=0)
    target_price = Column(DECIMAL(12, 2))
    coordinator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="forming", index=True)  # forming, ready, ordered, delivered
    deadline = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product")
    coordinator = relationship("User")
    participants = relationship("BulkBuyParticipant", back_populates="group")

class BulkBuyParticipant(Base):
    """Retailers participating in bulk buy"""
    __tablename__ = "bulk_buy_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("bulk_buy_groups.id"), nullable=False, index=True)
    retailer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    group = relationship("BulkBuyGroup", back_populates="participants")
    retailer = relationship("User")

class Referral(Base):
    """Customer referral tracking"""
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Candidate details (before they become a customer)
    referee_name = Column(String(255))
    referee_email = Column(String(255))
    referee_phone = Column(String(50))
    
    status = Column(String(20), default="pending", index=True) # pending, converted, rewarded
    reward_amount = Column(DECIMAL(12, 2), default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    converted_at = Column(DateTime(timezone=True))
    
    # Relationships
    referrer = relationship("Customer", foreign_keys=[referrer_id]) # back_populates removed for load simplicity

# ==================== POS OPERATIONS ====================

class DayClose(Base):
    """Daily cash register reconciliation"""
    __tablename__ = "day_close"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Opening
    opened_at = Column(DateTime(timezone=True), nullable=False)
    opened_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    opening_float = Column(DECIMAL(12, 2), nullable=False)
    
    # Closing
    closed_at = Column(DateTime(timezone=True))
    closed_by = Column(Integer, ForeignKey("users.id"))
    closing_float = Column(DECIMAL(12, 2))
    
    # Reconciliation
    expected_cash = Column(DECIMAL(12, 2))
    physical_cash = Column(DECIMAL(12, 2))
    variance = Column(DECIMAL(12, 2))  # Difference between expected and physical
    reconciliation_status = Column(String(50))  # matched, small_variance, large_variance
    
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ManagerOverride(Base):
    """Manager approvals for high-value operations"""
    __tablename__ = "manager_overrides"
    
    id = Column(Integer, primary_key=True, index=True)
    override_type = Column(String(50), nullable=False, index=True)  # discount, refund, price, quantity
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False, index=True)
    
    # Request details
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Cashier
    requested_amount = Column(DECIMAL(12, 2), nullable=False)
    request_reason = Column(String(500))
    
    # Approval
    approved_by = Column(Integer, ForeignKey("users.id"))  # Manager
    approval_status = Column(String(50), default="pending", index=True)  # pending, approved, rejected
    override_code = Column(String(8), unique=True, index=True)
    code_expires_at = Column(DateTime(timezone=True))
    code_used_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AuditLog(Base):
    """Audit trail for all manager actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50))  # sale, override, dayclose, etc
    entity_id = Column(Integer, index=True)
    
    details = Column(JSON)  # Context details as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    ip_address = Column(String(50))
