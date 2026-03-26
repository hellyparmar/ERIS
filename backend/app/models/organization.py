"""
organization.py - Organization and Store/Outlet Models
MSc Data Science Project - Enterprise Retail Intelligence System

Supports multi-outlet retail chains under a single organizational tenant.
"""

import uuid
import enum
from sqlalchemy import (
    Column, String, Boolean, ForeignKey,
    DateTime, Integer, Text, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Uuid, JSON

from .base import Base


# ── Enumerations ──────────────────────────────────────────────────────────────

class StoreType(enum.Enum):
    FLAGSHIP    = "flagship"
    BRANCH      = "branch"
    WAREHOUSE   = "warehouse"
    KIOSK       = "kiosk"


# ── Organization (Tenant) ─────────────────────────────────────────────────────

class Organization(Base):
    """
    Top-level tenant entity.
    All data (users, products, sales) is scoped to an organization.
    """
    __tablename__ = "organizations"

    id            = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identity
    name          = Column(String(255), nullable=False, index=True)
    legal_name    = Column(String(255))
    gstin         = Column(String(15),  unique=True)
    pan           = Column(String(10))

    # Contact
    contact_email = Column(String(255))
    contact_phone = Column(String(20))

    # Address stored as JSON for flexibility
    address       = Column(JSON, default=dict)

    # Subscription
    subscription_plan   = Column(String(50), default="starter", index=True)
    subscription_status = Column(String(20), default="trial")
    trial_ends_at       = Column(DateTime(timezone=True))
    subscription_ends_at = Column(DateTime(timezone=True))

    # Settings / branding
    logo_url      = Column(String(500))
    settings      = Column(JSON, default=lambda: {
        "currency":          "INR",
        "timezone":          "Asia/Kolkata",
        "date_format":       "DD/MM/YYYY",
        "fiscal_year_start": "04-01",
        "low_stock_threshold": 10,
    })

    # Status
    is_active     = Column(Boolean, default=True,  index=True)
    deleted_at    = Column(DateTime(timezone=True))

    # Timestamps
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    stores    = relationship("Store",    back_populates="organization", cascade="all, delete-orphan")
    users     = relationship("User",     back_populates="organization")
    products  = relationship("Product",  back_populates="organization")
    customers = relationship("Customer", back_populates="organization")

    __table_args__ = (
        Index("idx_org_plan_status", "subscription_plan", "subscription_status"),
    )

    def __repr__(self):
        return f"<Organization {self.name}>"


# ── Store / Outlet ────────────────────────────────────────────────────────────

class Store(Base):
    """
    Physical or virtual retail outlet.
    Each organization can manage multiple stores.
    """
    __tablename__ = "stores"

    id              = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    manager_id      = Column(Integer, ForeignKey("users.id",  ondelete="SET NULL"), index=True)

    # Identity
    name            = Column(String(255), nullable=False)
    code            = Column(String(50),  index=True)     # internal store code
    store_type      = Column(String(50),  default=StoreType.BRANCH.value, index=True)

    # Location
    address         = Column(JSON, default=dict)
    city            = Column(String(100), index=True)
    state           = Column(String(100))
    pincode         = Column(String(10))
    latitude        = Column(String(20))
    longitude       = Column(String(20))

    # Contact
    phone           = Column(String(20))
    email           = Column(String(255))

    # GST (outlet-level)
    gstin           = Column(String(15))

    # Capabilities
    has_pos         = Column(Boolean, default=True)
    has_inventory   = Column(Boolean, default=True)

    # Status
    is_active       = Column(Boolean, default=True, index=True)
    opened_at       = Column(DateTime(timezone=True))
    closed_at       = Column(DateTime(timezone=True))

    # Timestamps
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization    = relationship("Organization", back_populates="stores")
    manager         = relationship("User",         foreign_keys=[manager_id])
    staff           = relationship("UserStore",    back_populates="store")
    alerts          = relationship("Alert",        back_populates="store")

    __table_args__ = (
        Index("idx_store_org_active", "organization_id", "is_active"),
        Index("idx_store_city",       "city"),
    )

    def __repr__(self):
        return f"<Store {self.name} [{self.code}]>"
