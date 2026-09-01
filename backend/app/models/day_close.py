from sqlalchemy import Column, Integer, Float, String, Text, DateTime, Date, ForeignKey, func
from .base import Base

class DayClose(Base):
    __tablename__ = "day_closes"

    id = Column(Integer, primary_key=True, index=True)
    outlet_id = Column(Integer, ForeignKey("outlets.id"), nullable=False)
    date = Column(Date, nullable=False)
    opening_float = Column(Float, nullable=False)
    closing_float = Column(Float)
    expected_cash = Column(Float)
    physical_cash = Column(Float)
    variance = Column(Float)
    reconciliation_status = Column(String(50))
    notes = Column(Text)
    opened_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    closed_by = Column(Integer, ForeignKey("users.id"))
    opened_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    closed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
