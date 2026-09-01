from sqlalchemy import ForeignKey
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, func, text
from .base import Base

class Organization(Base):
    __tablename__ = "organizations"
    tenant_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    website = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    registration_number = Column(String(100), nullable=True)
    tax_id = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text('true'), default=True)
    is_deleted = Column(Boolean, nullable=False, server_default=text('false'), default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
