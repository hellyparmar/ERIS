"""
product.py - Product, Category, and Inventory Models
MSc Data Science Project - Enterprise Retail Intelligence System

Supports multi-outlet stock tracking with reorder alerts and full audit trails.
"""

import uuid
import enum
from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey,
    DateTime, DECIMAL, Text, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Uuid, JSON

from .base import Base


# ── Enumerations ──────────────────────────────────────────────────────────────

class ProductStatus(enum.Enum):
    ACTIVE       = "active"
    INACTIVE     = "inactive"
    DISCONTINUED = "discontinued"


class UnitOfMeasure(enum.Enum):
    PCS  = "pcs"
    KG   = "kg"
    GM   = "g"
    LTR  = "ltr"
    ML   = "ml"
    BOX  = "box"
    PACK = "pack"
    CASE = "case"


# ── Category ──────────────────────────────────────────────────────────────────

class Category(Base):
    """
    Product category (supports nested categories via parent_id).
    Scoped per organization.
    """
    __tablename__ = "categories"

    id              = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id       = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), index=True)

    name            = Column(String(150), nullable=False)
    slug            = Column(String(150), index=True)
    description     = Column(Text)
    image_url       = Column(String(500))

    is_active       = Column(Boolean, default=True)
    sort_order      = Column(Integer, default=0)

    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    parent          = relationship("Category", remote_side=[id], back_populates="children")
    children        = relationship("Category", back_populates="parent")
    products        = relationship("Product",  back_populates="category")

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_category_org_slug"),
        Index("idx_category_org", "organization_id", "is_active"),
    )

    def __repr__(self):
        return f"<Category {self.name}>"


# ── Product ───────────────────────────────────────────────────────────────────

class Product(Base):
    """
    Product (SKU) with pricing, cost, and stock levels.
    Inventory is tracked per organisation; per-store stock in StoreInventory.
    """
    __tablename__ = "products"

    id              = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id     = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), index=True)

    # Identification
    sku             = Column(String(100), nullable=False, index=True)
    barcode         = Column(String(100), index=True)
    name            = Column(String(255), nullable=False, index=True)
    description     = Column(Text)

    # Pricing
    price           = Column(DECIMAL(12, 2), nullable=False)      # selling price
    cost            = Column(DECIMAL(12, 2), nullable=False)      # purchase / COGS
    tax_rate        = Column(DECIMAL(5,  2), default=18.0)        # GST %

    # Stock
    stock           = Column(Integer, default=0)                  # aggregate stock
    reorder_level   = Column(Integer, default=10)                 # alert threshold
    max_stock       = Column(Integer)                             # max for order-up-to

    # Unit
    unit            = Column(String(20), default=UnitOfMeasure.PCS.value)

    # Metadata / extra attributes
    attributes      = Column(JSON, default=dict)    # colour, size, brand, etc.
    image_url       = Column(String(500))
    image_gallery   = Column(JSON, default=list)

    # Status
    status          = Column(String(20), default=ProductStatus.ACTIVE.value, index=True)
    is_active       = Column(Boolean, default=True, index=True)
    is_perishable   = Column(Boolean, default=False)
    expiry_days     = Column(Integer)

    # Timestamps
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at      = Column(DateTime(timezone=True))

    # Relationships
    organization    = relationship("Organization", back_populates="products")
    category        = relationship("Category",     back_populates="products")
    sale_items      = relationship("SaleItem",     back_populates="product")
    store_inventory = relationship("StoreInventory", back_populates="product")
    alerts          = relationship("Alert",        back_populates="product")

    __table_args__ = (
        UniqueConstraint("organization_id", "sku", name="uq_product_org_sku"),
        Index("idx_product_org_active",   "organization_id", "is_active"),
        Index("idx_product_category",     "category_id"),
        Index("idx_product_stock",        "stock", "reorder_level"),
    )

    @property
    def is_low_stock(self) -> bool:
        return self.stock <= self.reorder_level

    @property
    def margin_pct(self) -> float:
        if self.cost and self.cost > 0:
            return round(((float(self.price) - float(self.cost)) / float(self.price)) * 100, 2)
        return 0.0

    def __repr__(self):
        return f"<Product {self.sku}: {self.name}>"


# ── Store-Level Inventory ─────────────────────────────────────────────────────

class StoreInventory(Base):
    """
    Per-store stock quantities.
    Allows each outlet to have independent stock levels for the same product.
    """
    __tablename__ = "store_inventory"

    id         = Column(Integer, primary_key=True, index=True)
    store_id   = Column(Uuid(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    quantity        = Column(Integer, default=0)
    reorder_level   = Column(Integer, default=10)               # outlet-specific override
    reserved        = Column(Integer, default=0)                # held by pending orders
    last_restocked_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    product = relationship("Product", back_populates="store_inventory")

    __table_args__ = (
        UniqueConstraint("store_id", "product_id", name="uq_store_product"),
        Index("idx_store_inv_low", "quantity", "reorder_level"),
    )

    @property
    def available(self) -> int:
        return max(0, self.quantity - self.reserved)

    def __repr__(self):
        return f"<StoreInventory store={self.store_id} product={self.product_id} qty={self.quantity}>"
