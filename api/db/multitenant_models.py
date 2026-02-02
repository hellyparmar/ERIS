"""
Multi-Tenant Database Models
SQLAlchemy models for organizations and stores
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, TIMESTAMP, text, Index, Integer, Text, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from api.db.database import Base


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
    trial_ends_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW() + INTERVAL '30 days'"))
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

class User(Base):
    """Extended User model with organization"""
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    # ... existing fields ...
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    assigned_stores = Column(ARRAY(UUID(as_uuid=True)), default=[])
    
    # Relationship
    organization = relationship("Organization", back_populates="users")


class Product(Base):
    """Extended Product model with organization"""
    __tablename__ = 'products'
    __table_args__ = {'extend_existing': True}
    
    # ... existing fields ...
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    
    # Relationship
    organization = relationship("Organization", back_populates="products")


class Customer(Base):
    """Extended Customer model with organization"""
    __tablename__ = 'customers'
    __table_args__ = {'extend_existing': True}
    
    # ... existing fields ...
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    
    # Relationship
    organization = relationship("Organization", back_populates="customers")


class Supplier(Base):
    """Extended Supplier model with organization"""
    __tablename__ = 'suppliers'
    # No extend_existing because it does not exist in models.py
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    contact_person = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    gst_number = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    payment_terms_days = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Organization link
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    
    # Relationship
    organization = relationship("Organization", back_populates="suppliers")


class Invoice(Base):
    """Extended Invoice model with organization and store"""
    __tablename__ = 'invoices'
    __table_args__ = {'extend_existing': True}
    
    # ... existing fields ...
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False)
    
    # Relationships
    store = relationship("Store", back_populates="invoices")


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
    """Extended Inventory model with store"""
    __tablename__ = 'inventory'
    __table_args__ = {'extend_existing': True}
    
    # ... existing fields ...
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False)
    
    # Relationship
    store = relationship("Store", back_populates="inventory")
