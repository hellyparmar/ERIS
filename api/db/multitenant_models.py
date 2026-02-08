"""
Multi-Tenant Database Models
SQLAlchemy models for organizations and stores
"""

from sqlalchemy import (
    Column, String, Boolean, ForeignKey, TIMESTAMP, text, Index, Integer, Text, DECIMAL, DateTime, Float, Enum, Date
)
from sqlalchemy import (
    Column, String, Boolean, ForeignKey, TIMESTAMP, text, Index, Integer, Text, DECIMAL, DateTime, Float, Enum, Date, JSON
)
from sqlalchemy.types import Uuid
# For SQLite compatibility, we rename JSONB to JSON and handle ARRAY as JSON
JSONB = JSON
def ARRAY(item_type):
    return JSON
# UUID alias for compatibility if needed, though sqlalchemy.types.Uuid is preferred now
# We'll use standard UUID type from sqlalchemy which maps to CHAR(32) in SQLite
UUID = Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import sqlalchemy
from api.db.database import Base


import enum

class MessageChannel(enum.Enum):
    """Communication channels"""
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"

class Organization(Base):
    """
    Organization (tenant) model
    Each organization is a completely isolated tenant
    """
    __tablename__ = 'organizations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic Information
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255))
    gstin = Column(String(15), unique=True)
    pan = Column(String(10))
    
    # Address (JSON)
    address = Column(JSONB, default={})
    
    # Contact
    contact_email = Column(String(255))
    contact_phone = Column(String(20))
    
    # Subscription & Billing
    subscription_plan = Column(String(50), default='free')
    subscription_status = Column(String(20), default='trial')
    trial_ends_at = Column(TIMESTAMP(timezone=True))
    subscription_started_at = Column(TIMESTAMP(timezone=True))
    subscription_ends_at = Column(TIMESTAMP(timezone=True))
    
    # Billing
    billing_address = Column(JSONB, default={})
    upi_vpa = Column(String(100))
    
    # Settings
    settings = Column(JSONB, default={
        'currency': 'INR',
        'timezone': 'Asia/Kolkata',
        'date_format': 'DD/MM/YYYY',
        'fiscal_year_start': '04-01'
    })
    
    # Logo
    logo_url = Column(String(500))
    
    # Metadata
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    deleted_at = Column(TIMESTAMP(timezone=True))
    
    # Relationships
    stores = relationship("Store", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", back_populates="organization")
    products = relationship("Product", back_populates="organization")
    customers = relationship("Customer", back_populates="organization")
    suppliers = relationship("Supplier", back_populates="organization")
    invoices = relationship("Invoice", back_populates="organization")
    
    # Indexes
    __table_args__ = (
        Index('idx_organizations_gstin', 'gstin'),
        Index('idx_organizations_active', 'is_active'),
        Index('idx_organizations_plan', 'subscription_plan'),
    )
    
    def __repr__(self):
        return f"<Organization {self.name} ({self.subscription_plan})>"


class Store(Base):
    """
    Store/Location model
    Each organization can have multiple stores
    """
    __tablename__ = 'stores'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    
    # Basic Information
    name = Column(String(255), nullable=False)
    code = Column(String(50))
    
    # Address
    address = Column(JSONB, default={
        'line1': '',
        'line2': '',
        'city': '',
        'state': '',
        'state_code': '',
        'pincode': '',
        'country': 'India'
    })
    
    # Store Type
    store_type = Column(String(50), default='retail')
    
    # Contact
    manager_name = Column(String(255))
    contact_phone = Column(String(20))
    contact_email = Column(String(255))
    
    # Operating Hours
    operating_hours = Column(JSONB, default={
        'monday': {'open': '09:00', 'close': '21:00'},
        'tuesday': {'open': '09:00', 'close': '21:00'},
        'wednesday': {'open': '09:00', 'close': '21:00'},
        'thursday': {'open': '09:00', 'close': '21:00'},
        'friday': {'open': '09:00', 'close': '21:00'},
        'saturday': {'open': '09:00', 'close': '21:00'},
        'sunday': {'open': '10:00', 'close': '20:00'}
    })
    
    # Settings
    settings = Column(JSONB, default={})
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True))
    
    # Relationships
    organization = relationship("Organization", back_populates="stores")
    inventory = relationship("Inventory", back_populates="store")
    invoices = relationship("Invoice", back_populates="store")
    payments = relationship("Payment", back_populates="store")
    
    # Indexes & Constraints
    __table_args__ = (
        Index('idx_stores_org', 'organization_id'),
        Index('idx_stores_active', 'organization_id', 'is_active'),
        Index('idx_stores_type', 'store_type'),
    )
    
    def __repr__(self):
        return f"<Store {self.name} ({self.store_type})>"


# Update existing models to include organization/store relationships

import enum

class UserRole(enum.Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"
    ANALYST = "analyst"

class User(Base):
    """Extended User model with organization"""
    __tablename__ = 'users'
    # extend_existing not needed if this is the only definition, 
    # but harmless if we are sure no one else defines it. 
    # Let's keep it mostly clean.
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(sqlalchemy.Enum(UserRole), default=UserRole.ANALYST)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    assigned_stores = Column(ARRAY(UUID(as_uuid=True)), default=[])
    
    # Relationship
    organization = relationship("Organization", back_populates="users")
    # acknowledged_alerts = relationship("AlertAcknowledgment", back_populates="user")


class Product(Base):
    """Product catalog with Indian context"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), index=True)
    subcategory = Column(String(100), index=True)
    unit_price = Column(DECIMAL(12, 2), nullable=False)
    cost_price = Column(DECIMAL(12, 2))
    hsn_code = Column(String(50))
    gst_rate = Column(Float)
    
    # Dead Stock Management (NEW)
    is_dead_stock = Column(Boolean, default=False, index=True)
    last_sale_date = Column(DateTime(timezone=True))
    days_since_last_sale = Column(Integer)
    
    description = Column(Text)
    source = Column(String(50), default="manual")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Organization link
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    
    # Relationships
    inventory = relationship("Inventory", back_populates="product", uselist=False)
    alerts = relationship("Alert", back_populates="related_product")
    community_listings = relationship("CommunityListing", back_populates="product")
    sale_items = relationship("SaleItem", back_populates="product")
    organization = relationship("Organization", back_populates="products")


class Customer(Base):
    """Customer information with communication preferences"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String(100), unique=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    
    # WhatsApp Integration (NEW)
    whatsapp_number = Column(String(20))
    preferred_channel = Column(Enum(MessageChannel), default=MessageChannel.WHATSAPP)
    
    address = Column(Text)
    city = Column(String(100))
    country = Column(String(100))

    # Tally Integration
    tally_ledger_name = Column(String(255))  # Exact name of the Ledger in Tally
    
    # Loyalty Program (NEW)
    loyalty_points = Column(Integer, default=0)
    referral_code = Column(String(20), unique=True, index=True) # Unique code for inviting others
    
    # Credit Management (NEW)
    credit_allowed = Column(Boolean, default=False, index=True)
    
    # Advanced AI Analytics (R-DIOS Enterprise Features)
    churn_risk_score = Column(Float, default=0.0) # 0.0 to 1.0 (1.0 = High Risk)
    customer_segment = Column(String(50), default="New") # Whale, Loyal, At Risk, Churned, New
    
    source = Column(String(50), default="manual")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Organization link
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    
    # Relationships
    sales = relationship("Sale", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")
    credit_account = relationship("CustomerCredit", back_populates="customer", uselist=False)
    organization = relationship("Organization", back_populates="customers")



class PurchaseOrder(Base):
    """Purchase orders from suppliers"""
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    order_date = Column(Date, nullable=False, server_default=func.current_date())
    expected_delivery_date = Column(Date)
    actual_delivery_date = Column(Date)
    
    subtotal = Column(DECIMAL(15, 2), nullable=False)
    gst_amount = Column(DECIMAL(15, 2), default=0)
    total_amount = Column(DECIMAL(15, 2), nullable=False)
    
    status = Column(String(50), default="draft", index=True)
    is_auto_generated = Column(Boolean, default=False)
    trigger_reason = Column(String(100))
    
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Organization link
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order")
    organization = relationship("Organization")
    store = relationship("Store")


class PurchaseOrderItem(Base):
    """Line items for purchase orders"""
    __tablename__ = "purchase_order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    quantity_ordered = Column(Integer, nullable=False)
    quantity_received = Column(Integer, default=0)
    unit_cost = Column(DECIMAL(15, 2), nullable=False)
    gst_rate = Column(DECIMAL(5, 2), nullable=False)
    line_total = Column(DECIMAL(15, 2), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")


class Supplier(Base):
    """Supplier vendor model"""
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_code = Column(String(100), unique=True, index=True)
    name = Column(String(255), nullable=False)
    contact_person = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    gst_number = Column(String(20))
    
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    
    payment_terms_days = Column(Integer, default=30) # e.g. Net 30
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Organization link
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    
    # Relationship
    organization = relationship("Organization", back_populates="suppliers")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")


class PaymentStatus(enum.Enum):
    """Invoice payment status"""
    PAID = "paid"
    PARTIAL = "partial"
    PENDING = "pending"
    OVERDUE = "overdue"

class Invoice(Base):
    """Invoices with GST automation and multi-tenant support"""
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # GST/Tax Automation
    hsn_code = Column(String(10))
    tax_rate = Column(DECIMAL(5, 2))
    taxable_amount = Column(DECIMAL(12, 2))
    tax_amount = Column(DECIMAL(12, 2))
    total_amount = Column(DECIMAL(12, 2), nullable=False)
    
    # Khata/Credit Management
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, index=True)
    amount_paid = Column(DECIMAL(12, 2), default=0.0)
    amount_due = Column(DECIMAL(12, 2))

    # Tally Prime Integration
    tally_sync_status = Column(String(20), default="pending", index=True)  # pending, synced, failed
    tally_voucher_number = Column(String(50))  # VchNo in Tally
    tally_error_log = Column(Text)  # Last error message if failed
    
    # Digital Receipts
    receipt_sent_via = Column(String(20))  # whatsapp, email, sms
    receipt_url = Column(Text)
    
    invoice_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    due_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Organization link
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    sales = relationship("Sale", back_populates="invoice")
    payments = relationship("InvoicePayment", back_populates="invoice")
    # messages relationship omitted to avoid circular dependency loop if complex, referencing Message via string usually works though.
    store = relationship("Store", back_populates="invoices")
    organization = relationship("Organization", back_populates="invoices")


class Payment(Base):
    """Extended Payment model with organization and store"""
    __tablename__ = 'payments'
    # No extend_existing because it does not exist in models.py (only InvoicePayment exists there)
    
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(DECIMAL(12, 2), nullable=False)
    payment_date = Column(TIMESTAMP(timezone=True), server_default=func.now())
    payment_method = Column(String(50))
    reference_number = Column(String(100))
    notes = Column(Text)
    
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'))
    
    # Relationship
    store = relationship("Store", back_populates="payments")


class Inventory(Base):
    """Inventory levels with enriched tracking"""
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False)
    
    # Stock Management
    current_stock = Column(Integer, default=0)
    reserved_stock = Column(Integer, default=0)
    available_stock = Column(Integer, default=0)
    
    # Reorder Management (UPDATED)
    reorder_point = Column(Integer, default=10)
    reorder_quantity = Column(Integer, default=50)
    max_stock_level = Column(Integer)  # NEW
    
    warehouse_location = Column(String(100))
    
    # Timestamps (UPDATED)
    last_stocked_date = Column(DateTime(timezone=True))
    last_restocked = Column(DateTime(timezone=True))  # NEW
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Store link
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False)
    
    # Relationships
    product = relationship("Product", back_populates="inventory")
    store = relationship("Store", back_populates="inventory")



