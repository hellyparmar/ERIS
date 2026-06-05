"""
customers.py - Customer Model
MSc Data Science Project - Enterprise Retail Intelligence System

Supports B2B and B2C customers with loyalty, credit, and transaction history.
"""

import uuid
from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey,
    DateTime, DECIMAL, Text, Index, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Uuid

from .base import Base


# ── Customer ──────────────────────────────────────────────────────────────────

class Customer(Base):
    """
    Retail customer (B2C / B2B) with contact, address, credit, and loyalty tracking.
    Scoped per organization.
    """
    __tablename__ = "customers"
    __table_args__ = {'extend_existing': True}

    id              = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Identification
    name            = Column(String(255), nullable=False, index=True)
    phone           = Column(String(20), nullable=False, unique=True, index=True)
    email           = Column(String(255), index=True)
    gstin           = Column(String(15))                       # for B2B

    # Address
    address         = Column(JSON, default=dict)
    city            = Column(String(100), index=True)
    state           = Column(String(100))
    pincode         = Column(String(10))

    # Credit limit & account
    credit_limit    = Column(DECIMAL(12, 2), default=0)       # max credit allowed
    credit_used     = Column(DECIMAL(12, 2), default=0)       # outstanding credit balance
    credit_available = Column(DECIMAL(12, 2), default=0)

    # Loyalty program
    loyalty_points  = Column(Integer, default=0)
    loyalty_tier    = Column(String(50), default="standard")  # bronze, silver, gold, platinum
    total_spent     = Column(DECIMAL(14, 2), default=0)       # lifetime LTV

    # Classification
    customer_type   = Column(String(20), default="b2c")       # b2c, b2b, walk-in
    is_active       = Column(Boolean, default=True, index=True)
    is_blacklisted  = Column(Boolean, default=False)

    # Contact preferences
    allow_sms       = Column(Boolean, default=True)
    allow_email     = Column(Boolean, default=True)
    allow_calls     = Column(Boolean, default=True)

    # KYC / metadata
    kyc_verified    = Column(Boolean, default=False)
    kyc_verified_at = Column(DateTime(timezone=True))
    extra_data      = Column(JSON, default=dict)               # custom fields, preferences

    # Timestamps
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())
    last_purchase_at = Column(DateTime(timezone=True))
    deleted_at      = Column(DateTime(timezone=True))         # soft-delete

    organization    = relationship("Organization")
    sales           = relationship("Sale", back_populates="customer")

    __table_args__ = (
        UniqueConstraint("organization_id", "phone", name="uq_customer_org_phone"),
        Index("idx_customer_org_active",   "organization_id", "is_active"),
        Index("idx_customer_loyalty",      "loyalty_tier"),
        Index("idx_customer_credit",       "credit_available"),
    )

    @property
    def credit_percentage(self) -> float:
        """Return percentage of credit limit used."""
        if self.credit_limit == 0:
            return 0.0
        return round((float(self.credit_used) / float(self.credit_limit)) * 100, 2)

    def __repr__(self):
        return f"<Customer {self.name} [{self.phone}]>"
