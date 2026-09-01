from sqlalchemy import Column, Integer, String, DateTime, func, JSON
from .base import Base

class AuditLogEntry(Base):
    __tablename__ = "audit_log_entries"
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100))
    performed_by = Column(Integer)
    approved_by = Column(Integer, nullable=True)
    context = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
