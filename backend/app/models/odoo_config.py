from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Text, func
from app.models.base import Base

class OdooConfig(Base):
    """Odoo ERP Integration Configuration"""
    __tablename__ = "odoo_configs"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, default=1, index=True)
    url = Column(String(500), nullable=False)
    database_name = Column(String(200), nullable=False)
    username = Column(String(200), nullable=False)
    api_key = Column(Text, nullable=False)
    sync_products = Column(Boolean, default=True, nullable=False)
    sync_customers = Column(Boolean, default=True, nullable=False)
    sync_invoices = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
