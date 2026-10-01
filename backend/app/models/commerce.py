"""Product, supplier, sale, and stock-movement models."""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, ForeignKey, DECIMAL, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


BIGINT_PRIMARY_KEY = BigInteger().with_variant(Integer, "sqlite")


# ============================================================
# CORE MODELS
# ============================================================


class Supplier(Base):
    """B2B supplier management"""

    __tablename__ = "suppliers"

    id = Column(BIGINT_PRIMARY_KEY, primary_key=True, autoincrement=True)
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
    id = Column(BIGINT_PRIMARY_KEY, primary_key=True, autoincrement=True)
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

    # Outlet quantities live in the inventory table.
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
        Index("idx_products_active", is_active, is_deleted),
    )


# ============================================================
# TRANSACTIONAL MODELS
# ============================================================


class Sale(Base):
    """Outlet sales transactions."""

    __tablename__ = "sales"
    id = Column(BIGINT_PRIMARY_KEY, primary_key=True, autoincrement=True)
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
    payment_method = Column(String(20), nullable=False)
    payment_status = Column(String(20), nullable=False, default="pending")
    amount_paid = Column(DECIMAL(12, 2), nullable=False, default=0)
    status = Column(String(20), nullable=False, default="initiated")
    channel = Column(String(20), nullable=False, default="offline")
    notes = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="sales")
    user = relationship("User")
    items = relationship("SaleItem", back_populates="sale")
    payments = relationship("Payment", back_populates="sale")

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
        CheckConstraint(
            "payment_method IN ('cash', 'card', 'upi', 'netbanking', 'wallet', 'credit')",
            name="ck_sales_payment_method",
        ),
        CheckConstraint(
            "payment_status IN ('pending', 'paid', 'failed', 'refunded', 'partial')", name="ck_sales_payment_status"
        ),
        CheckConstraint("status IN ('initiated', 'completed', 'cancelled', 'refunded')", name="ck_sales_status"),
        CheckConstraint("channel IN ('offline', 'online', 'manual')", name="ck_sales_channel"),
        Index("idx_sales_date", sale_date),
        Index("idx_sales_customer", customer_id, sale_date),
    )


class SaleItem(Base):
    """Line items for sales"""

    __tablename__ = "sale_items"

    id = Column(BIGINT_PRIMARY_KEY, primary_key=True, autoincrement=True)
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


class StockMovement(Base):
    """Inventory audit trail"""

    __tablename__ = "stock_movements"

    id = Column(BIGINT_PRIMARY_KEY, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, nullable=False, default=1)
    outlet_id = Column(Integer, ForeignKey("outlets.id", ondelete="CASCADE"), nullable=False)
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
        CheckConstraint(
            "movement_type IN ('sale', 'purchase', 'return', 'adjustment', 'transfer', 'shrinkage')",
            name="ck_stock_movement_type",
        ),
        Index("idx_stock_movement_outlet_product", outlet_id, product_id, created_at),
    )
