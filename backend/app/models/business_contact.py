"""
business_contact.py - BusinessContact model
"""

import uuid
import enum
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Enum as SqlEnum,
    Index, ARRAY, JSON, func, UUID
)
from sqlalchemy.orm import relationship
from .base import Base


class ContactType(enum.Enum):
    supplier = "supplier"
    distributor = "distributor"
    logistics = "logistics"


class BusinessContact(Base):
    __tablename__ = "business_contacts"

    contact_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    company_name = Column(String(255), nullable=False)
    contact_person = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    gst_number = Column(String(15))
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    contact_type = Column(SqlEnum(ContactType), nullable=False)
    product_categories = Column(ARRAY(String).with_variant(JSON, "sqlite"), default=list)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    invoices = relationship("Invoice", back_populates="contact")

    __table_args__ = (
        Index("idx_business_contacts_contact_type", "contact_type"),
        Index("idx_business_contacts_is_active", "is_active"),
    )
