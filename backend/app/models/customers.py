"""
customers.py - Customer Model
MSc Data Science Project - Enterprise Retail Intelligence System

    Supports B2B and B2C customers with transaction history.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, UniqueConstraint, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


# ── Customer ──────────────────────────────────────────────────────────────────


class Customer(Base):
    """
    Retail customer (B2C / B2B) with contact and address tracking.
    Scoped per organization.
    """

    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Identification
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(120), nullable=True, index=True)
    phone = Column(String(20), nullable=True, index=True)
    gst_number = Column(String(15), nullable=True)  # for B2B

    # Address
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)

    total_purchases = Column(Numeric(12, 2), nullable=False, default=0)
    total_transactions = Column(Integer, nullable=False, default=0)

    # Classification
    customer_type = Column(String(50), default="retail", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    organization = relationship("Organization")
    sales = relationship("Sale", back_populates="customer")

    __table_args__ = (
        UniqueConstraint("organization_id", "phone", name="uq_customer_org_phone"),
        Index("idx_customer_org_active", "organization_id", "is_active"),
    )

    # Derived presentation fields used by the customer APIs.
    @property
    def name(self) -> str:
        return " ".join(part for part in (self.first_name, self.last_name) if part).strip()

    @name.setter
    def name(self, value: str) -> None:
        parts = (value or "").strip().split(maxsplit=1)
        self.first_name = parts[0] if parts else "Customer"
        self.last_name = parts[1] if len(parts) > 1 else ""

    @property
    def total_spent(self):
        return self.total_purchases or 0

    @property
    def segment(self) -> str:
        if self.total_spent and float(self.total_spent) >= 50000:
            return "VIP"
        elif self.total_spent and float(self.total_spent) >= 10000:
            return "Regular"
        return "New"

    @property
    def lifetime_value(self):
        return self.total_spent or 0

    @property
    def first_purchase_at(self):
        return self.created_at

    @property
    def last_purchase_at(self):
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "address": self.address if isinstance(self.address, str) else str(self.address or ""),
            "segment": self.segment,
            "lifetime_value": float(self.lifetime_value) if self.lifetime_value else 0,
            "total_purchases": self.total_transactions,
            "total_spent": float(self.total_spent),
            "first_purchase_at": self.first_purchase_at.isoformat() if self.first_purchase_at else None,
            "last_purchase_at": self.last_purchase_at.isoformat() if self.last_purchase_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Customer {self.name} [{self.phone}]>"
