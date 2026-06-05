"""
Simplified Outlet model matching the current database schema.
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, Float, DateTime, func
from .base import Base

class Outlet(Base):
    __tablename__ = "outlets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    outlet_type = Column(String(20), default="standard")
    address = Column(Text)
    pincode = Column(String(10))
    phone = Column(String(15))
    is_active = Column(Boolean, default=True)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Outlet {self.name}>"