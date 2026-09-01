from sqlalchemy import ForeignKey
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Time, func, text, Float
from .base import Base

class Outlet(Base):
    __tablename__ = "outlets"
    tenant_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, default=1)
    name = Column(String(200), nullable=False)
    code = Column(String(50))
    address = Column(String(500))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100), default="India")
    postal_code = Column(String(20))
    phone = Column(String(20))
    email = Column(String(120), nullable=True)
    opening_time = Column(Time)
    closing_time = Column(Time)
    is_active = Column(Boolean, nullable=False, server_default=text('true'), default=True)
    is_deleted = Column(Boolean, nullable=False, server_default=text('false'), default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    @property
    def outlet_type(self) -> str:
        return self.code or "standard"

    @property
    def pincode(self) -> str:
        return self.postal_code or ""

    @pincode.setter
    def pincode(self, value: str):
        self.postal_code = value

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    def __repr__(self):
        return f"<Outlet {self.name}>"