from sqlalchemy import ForeignKey
import uuid
from sqlalchemy.dialects.postgresql import UUID
"""
R-DIOS v6.0 SQLAlchemy Models
Comprehensive ORM models for thesis database schema
"""

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, Date, ForeignKey, DECIMAL, CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


# ============================================================
# CORE MODELS
# ============================================================



class Supplier(Base):
    """B2B supplier management"""
    __tablename__ = "suppliers"
    
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    contact_person = Column(String(200))
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
    organization_id = Column(Integer, nullable=False, default=1)
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
    tenant_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(Integer, nullable=False, default=1)
    category_id = Column(Integer, ForeignKey("product_categories.id"))
    supplier_id = Column(BigInteger, ForeignKey("suppliers.id"))
    
    # Identification
    sku = Column(String(50), unique=True)
    name = Column(String(300), nullable=False)
    description = Column(Text)
    
    # Pricing
    cost_price = Column(DECIMAL(10, 2), nullable=False)
    selling_price = Column(DECIMAL(10, 2), nullable=False)
    mrp = Column(DECIMAL(10, 2))
    
    # Tax
    hsn_code = Column(String(8))
    
    # Inventory
    current_stock = Column(Integer, default=0, nullable=False)
    reorder_level = Column(Integer, default=10, nullable=False)
    reorder_quantity = Column(Integer, default=50, nullable=False)
    
    # Attributes
    unit = Column(String(50))
    barcode = Column(String(100))
    is_perishable = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    category = relationship("ProductCategory", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    sale_items = relationship("SaleItem", back_populates="product")
    stock_movements = relationship("StockMovement", back_populates="product")
    
    __table_args__ = (
        CheckConstraint("cost_price >= 0", name="check_cost_price_non_negative"),
        CheckConstraint("selling_price > 0", name="check_selling_price_positive"),
        Index("idx_products_stock", current_stock, reorder_level),
    )


# ============================================================
# TRANSACTIONAL MODELS
# ============================================================

class Sale(Base):
    """Sales transactions (partitioned by quarter)"""
    __tablename__ = "sales"
    tenant_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, nullable=False, default=1)
    outlet_id = Column(Integer, ForeignKey("outlets.id"), nullable=False)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="SET NULL"))
    user_id = Column(BigInteger, ForeignKey("users.id"))
    
    sale_number = Column(String(50), nullable=False, unique=True)
    sale_date = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    # Amounts
    subtotal = Column(DECIMAL(12, 2), nullable=False)
    tax_amount = Column(DECIMAL(12, 2), nullable=False, default=0)
    discount_amount = Column(DECIMAL(12, 2), nullable=False, default=0)
    total_amount = Column(DECIMAL(12, 2), nullable=False)
    
    # Payment
    payment_method = Column(ENUM('cash', 'card', 'upi', 'netbanking', 'wallet', 'credit', name='paymentmethodenum', create_type=False), nullable=False)
    payment_status = Column(ENUM('PENDING', 'PAID', 'FAILED', 'REFUNDED', 'PARTIAL', name='paymentstatusenum', create_type=False), nullable=False, default="PENDING")
    amount_paid = Column(DECIMAL(12, 2), nullable=False, default=0)
    status = Column(ENUM('INITIATED', 'COMPLETED', 'CANCELLED', 'REFUNDED', name='salestatusenum', create_type=False), nullable=False, default="INITIATED")
    channel = Column(String(20), nullable=False, default="offline")
    notes = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="sales")
    user = relationship("User")
    items = relationship("SaleItem", back_populates="sale")
    payments = relationship("Payment", back_populates="sale")

    # Backward-compatibility aliases for legacy SaleTransaction queries
    @property
    def transaction_at(self):
        return self.sale_date

    @transaction_at.setter
    def transaction_at(self, val):
        self.sale_date = val

    @property
    def transaction_date(self):
        return self.sale_date

    @property
    def cashier_id(self):
        return self.user_id

    @cashier_id.setter
    def cashier_id(self, val):
        self.user_id = val

    @property
    def store_id(self):
        return self.outlet_id

    @store_id.setter
    def store_id(self, val):
        self.outlet_id = val

    @property
    def gst_amount(self):
        return self.tax_amount

    @gst_amount.setter
    def gst_amount(self, val):
        self.tax_amount = val

    @property
    def transaction_id(self):
        return self.sale_number or str(self.id)
    
    __table_args__ = (
        CheckConstraint("payment_method IN ('cash', 'upi', 'card', 'mixed')", name="ck_sales_payment_method"),
        CheckConstraint("payment_status IN ('pending', 'partial', 'paid', 'overdue')", name="ck_sales_payment_status"),
        CheckConstraint("channel IN ('offline', 'online')", name="ck_sales_channel"),
        Index("idx_sales_date", sale_date),
        Index("idx_sales_customer", customer_id, sale_date),
        {'extend_existing': True}
    )


class SaleItem(Base):
    """Line items for sales"""
    __tablename__ = "sale_items"
    
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(Integer, nullable=False, default=1)
    sale_id = Column(BigInteger, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="RESTRICT"))
    
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    discount_percent = Column(DECIMAL(5, 2), default=0, nullable=False)
    line_total = Column(DECIMAL(12, 2), nullable=False)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")
    
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_sale_items_quantity"),
        Index("idx_sale_items_product", product_id),
    )


# ============================================================
# PROCUREMENT MODELS
# ============================================================

class PurchaseOrder(Base):
    """Purchase orders from suppliers"""
    __tablename__ = "purchase_orders"
    
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(Integer, nullable=False, default=1)
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


class SchemaVersion(Base):
    """Database schema version tracking"""
    __tablename__ = "schema_version"
    
    version = Column(String(20), primary_key=True)
    applied_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    description = Column(Text)
