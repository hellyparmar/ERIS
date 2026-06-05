"""
R-DIOS v6.0 SQLAlchemy Models
Comprehensive ORM models for thesis database schema
"""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, Date, DateTime,
    ForeignKey, DECIMAL, CheckConstraint, UniqueConstraint, Index, JSON
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# ============================================================
# CORE MODELS
# ============================================================

class User(Base):
    """User authentication and authorization"""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user")
    is_active = Column(Boolean, default=True)
    last_login = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    sales = relationship("Sale", back_populates="user")
    
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'manager', 'cashier', 'user')", name="ck_users_role"),
    )


class Customer(Base):
    """B2C customer management with RFM analytics"""
    __tablename__ = "customers"
    __table_args__ = {'extend_existing': True}
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"))
    name = Column(String(200), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    whatsapp = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(10))
    
    # Credit/Khata
    credit_limit = Column(DECIMAL(15, 2), default=0)
    outstanding_amount = Column(DECIMAL(15, 2), default=0)
    credit_score = Column(Integer, default=100)
    
    # RFM Analytics
    last_purchase_date = Column(Date)
    purchase_count = Column(Integer, default=0)
    total_spent = Column(DECIMAL(15, 2), default=0)
    rfm_segment = Column(String(50))
    
    # Personal
    date_of_birth = Column(Date)
    anniversary_date = Column(Date)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    sales = relationship("Sale", back_populates="customer")
    credit_accounts = relationship("CreditAccount", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")
    
    __table_args__ = (
        CheckConstraint("credit_score BETWEEN 0 AND 100", name="ck_customers_credit_score"),
        Index("idx_customers_phone", phone),
        Index("idx_customers_rfm", last_purchase_date, purchase_count, total_spent),
    )


class Supplier(Base):
    """B2B supplier management"""
    __tablename__ = "suppliers"
    
    id = Column(BigInteger, primary_key=True)
    name = Column(String(200), nullable=False)
    contact_person = Column(String(200))
    email = Column(String(255))
    phone = Column(String(20))
    gst_number = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(10))
    
    # Performance
    avg_lead_time_days = Column(Integer, default=7)
    quality_rating = Column(DECIMAL(3, 2), default=5.0)
    on_time_delivery_rate = Column(DECIMAL(5, 2), default=100)
    
    # Financial
    payment_terms_days = Column(Integer, default=30)
    outstanding_payable = Column(DECIMAL(15, 2), default=0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    products = relationship("Product", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")


class ProductCategory(Base):
    """Product categories with GST rates"""
    __tablename__ = "product_categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("product_categories.id"))
    hsn_code = Column(String(20))
    default_gst_rate = Column(DECIMAL(5, 2), default=18.00)
    avg_margin = Column(DECIMAL(5, 2), default=25.00)
    dead_stock_days = Column(Integer, default=180)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Self-referential
    parent = relationship("ProductCategory", remote_side=[id])
    products = relationship("Product", back_populates="category")


class Product(Base):
    """Product catalog with inventory tracking"""
    __tablename__ = "products"
    
    id = Column(BigInteger, primary_key=True)
    category_id = Column(Integer, ForeignKey("product_categories.id"))
    supplier_id = Column(BigInteger, ForeignKey("suppliers.id"))
    
    # Identification
    sku = Column(String(50), unique=True)
    barcode = Column(String(50))
    name = Column(String(300), nullable=False)
    description = Column(Text)
    
    # Pricing
    cost_price = Column(DECIMAL(15, 2), nullable=False)
    selling_price = Column(DECIMAL(15, 2), nullable=False)
    mrp = Column(DECIMAL(15, 2))
    
    # Tax
    hsn_code = Column(String(20), nullable=False)
    gst_rate = Column(DECIMAL(5, 2), nullable=False, default=18.00)
    
    # Inventory
    stock_level = Column(Integer, default=0)
    reorder_point = Column(Integer, default=10)
    min_order_quantity = Column(Integer, default=1)
    max_stock_level = Column(Integer, default=1000)
    
    # Variants
    has_variants = Column(Boolean, default=False)
    variants = Column(JSONB)
    
    # Analytics
    last_sale_date = Column(Date)
    last_restock_date = Column(Date)
    total_units_sold = Column(Integer, default=0)
    abc_classification = Column(String(1))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    category = relationship("ProductCategory", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    sale_items = relationship("SaleItem", back_populates="product")
    stock_movements = relationship("StockMovement", back_populates="product")
    
    __table_args__ = (
        CheckConstraint("abc_classification IN ('A', 'B', 'C')", name="ck_products_abc"),
        Index("idx_products_stock", stock_level, reorder_point),
    )


# ============================================================
# TRANSACTIONAL MODELS
# ============================================================

class Sale(Base):
    """Sales transactions (partitioned by quarter)"""
    __tablename__ = "sales"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="SET NULL"))
    user_id = Column(BigInteger, ForeignKey("users.id"))
    
    invoice_number = Column(String(50), unique=True)
    sale_date = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), primary_key=True)
    
    # Amounts
    subtotal = Column(DECIMAL(15, 2), nullable=False)
    gst_amount = Column(DECIMAL(15, 2), default=0)
    discount_amount = Column(DECIMAL(15, 2), default=0)
    total_amount = Column(DECIMAL(15, 2), nullable=False)
    
    # Payment
    payment_method = Column(String(50))
    payment_status = Column(String(50), default="pending")
    amount_paid = Column(DECIMAL(15, 2), default=0)
    amount_due = Column(DECIMAL(15, 2), default=0)
    split_payment = Column(JSONB)
    
    # Causal factors
    channel = Column(String(50), default="offline")
    promotion_code = Column(String(50))
    weather_temperature = Column(DECIMAL(5, 2))
    weather_condition = Column(String(50))
    is_holiday = Column(Boolean, default=False)
    holiday_name = Column(String(100))
    
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="sales")
    user = relationship("User", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale")
    payments = relationship("Payment", back_populates="sale")
    
    __table_args__ = (
        CheckConstraint("payment_method IN ('cash', 'upi', 'card', 'credit', 'mixed')", name="ck_sales_payment_method"),
        CheckConstraint("payment_status IN ('pending', 'partial', 'paid', 'overdue')", name="ck_sales_payment_status"),
        CheckConstraint("channel IN ('offline', 'online', 'whatsapp')", name="ck_sales_channel"),
        Index("idx_sales_date", sale_date),
        Index("idx_sales_customer", customer_id, sale_date),
    )


class SaleItem(Base):
    """Line items for sales"""
    __tablename__ = "sale_items"
    
    id = Column(BigInteger, primary_key=True)
    sale_id = Column(BigInteger, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    sale_date = Column(TIMESTAMP(timezone=True), nullable=False)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="RESTRICT"))
    
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(15, 2), nullable=False)
    discount_percent = Column(DECIMAL(5, 2), default=0)
    discount_amount = Column(DECIMAL(15, 2), default=0)
    gst_rate = Column(DECIMAL(5, 2), nullable=False)
    gst_amount = Column(DECIMAL(15, 2), nullable=False)
    line_total = Column(DECIMAL(15, 2), nullable=False)
    
    variant_sku = Column(String(50))
    variant_details = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")
    
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_sale_items_quantity"),
        Index("idx_sale_items_product", product_id, sale_date),
    )


class Payment(Base):
    """Payment transactions"""
    __tablename__ = "payments"
    
    id = Column(BigInteger, primary_key=True)
    sale_id = Column(BigInteger)
    sale_date = Column(TIMESTAMP(timezone=True))
    customer_id = Column(BigInteger, ForeignKey("customers.id"))
    
    payment_date = Column(TIMESTAMP(timezone=True), server_default=func.now())
    amount = Column(DECIMAL(15, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)
    reference_number = Column(String(100))
    split_payment = Column(JSONB)
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    sale = relationship("Sale", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")


class CreditAccount(Base):
    """Khata/Credit ledger"""
    __tablename__ = "credit_accounts"
    
    id = Column(BigInteger, primary_key=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="RESTRICT"))
    sale_id = Column(BigInteger)
    sale_date = Column(TIMESTAMP(timezone=True))
    
    amount = Column(DECIMAL(15, 2), nullable=False)
    amount_paid = Column(DECIMAL(15, 2), default=0)
    due_date = Column(Date, nullable=False)
    
    status = Column(String(50), default="pending")
    last_payment_date = Column(Date)
    reminder_count = Column(Integer, default=0)
    last_reminder_date = Column(Date)
    
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    closed_date = Column(TIMESTAMP(timezone=True))
    
    # Relationships
    customer = relationship("Customer", back_populates="credit_accounts")
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'partial', 'paid', 'overdue', 'written_off')", name="ck_credit_status"),
    )


# ============================================================
# PROCUREMENT MODELS
# ============================================================

class PurchaseOrder(Base):
    """Purchase orders from suppliers"""
    __tablename__ = "purchase_orders"
    
    id = Column(BigInteger, primary_key=True)
    supplier_id = Column(BigInteger, ForeignKey("suppliers.id", ondelete="RESTRICT"))
    user_id = Column(BigInteger, ForeignKey("users.id"))
    
    po_number = Column(String(50), unique=True, nullable=False)
    order_date = Column(Date, nullable=False, server_default=func.current_date())
    expected_delivery_date = Column(Date)
    actual_delivery_date = Column(Date)
    
    subtotal = Column(DECIMAL(15, 2), nullable=False)
    gst_amount = Column(DECIMAL(15, 2), default=0)
    total_amount = Column(DECIMAL(15, 2), nullable=False)
    
    status = Column(String(50), default="draft")
    is_auto_generated = Column(Boolean, default=False)
    trigger_reason = Column(String(100))
    
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order")


class PurchaseOrderItem(Base):
    """Line items for purchase orders"""
    __tablename__ = "purchase_order_items"
    
    id = Column(BigInteger, primary_key=True)
    purchase_order_id = Column(BigInteger, ForeignKey("purchase_orders.id", ondelete="CASCADE"))
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="RESTRICT"))
    
    quantity_ordered = Column(Integer, nullable=False)
    quantity_received = Column(Integer, default=0)
    unit_cost = Column(DECIMAL(15, 2), nullable=False)
    gst_rate = Column(DECIMAL(5, 2), nullable=False)
    line_total = Column(DECIMAL(15, 2), nullable=False)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="items")


class StockMovement(Base):
    """Inventory audit trail"""
    __tablename__ = "stock_movements"
    
    id = Column(BigInteger, primary_key=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"))
    
    movement_type = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    
    reference_type = Column(String(50))
    reference_id = Column(BigInteger)
    
    stock_before = Column(Integer, nullable=False)
    stock_after = Column(Integer, nullable=False)
    
    user_id = Column(BigInteger, ForeignKey("users.id"))
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="stock_movements")
    
    __table_args__ = (
        CheckConstraint("movement_type IN ('sale', 'purchase', 'return', 'adjustment', 'transfer', 'shrinkage')", name="ck_stock_movement_type"),
    )


# ============================================================
# EXTERNAL FACTORS (For Causal Analysis)
# ============================================================

class WeatherData(Base):
    """Weather data for causal analysis"""
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True)
    city = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    
    temperature_high = Column(DECIMAL(5, 2))
    temperature_low = Column(DECIMAL(5, 2))
    temperature_avg = Column(DECIMAL(5, 2))
    precipitation_mm = Column(DECIMAL(7, 2), default=0)
    humidity_percent = Column(Integer)
    condition = Column(String(50))
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint("city", "date", name="uq_weather_city_date"),
    )


class Holiday(Base):
    """Holiday calendar for causal analysis"""
    __tablename__ = "holidays"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(50))
    region = Column(String(100))
    is_major = Column(Boolean, default=False)
    expected_impact_percent = Column(DECIMAL(5, 2))
    
    __table_args__ = (
        UniqueConstraint("date", "name", name="uq_holiday_date_name"),
        CheckConstraint("type IN ('national', 'regional', 'religious', 'observance')", name="ck_holiday_type"),
    )


class EconomicIndicator(Base):
    """Economic indicators for causal analysis"""
    __tablename__ = "economic_indicators"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, nullable=False)
    
    cpi_inflation = Column(DECIMAL(5, 2))
    wpi_inflation = Column(DECIMAL(5, 2))
    fuel_price_petrol = Column(DECIMAL(7, 2))
    fuel_price_diesel = Column(DECIMAL(7, 2))
    gold_price = Column(DECIMAL(10, 2))
    usd_inr_rate = Column(DECIMAL(7, 2))
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


# ============================================================
# SCHEMA VERSION TRACKING
# ============================================================

class SchemaVersion(Base):
    """Database schema version tracking"""
    __tablename__ = "schema_version"
    
    version = Column(String(20), primary_key=True)
    applied_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    description = Column(Text)
