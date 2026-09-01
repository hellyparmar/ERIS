from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Text, DECIMAL, func
from app.models.base import Base

class CommunityListing(Base):
    """Community Marketplace and Bulletin Board Listing"""
    __tablename__ = "community_listings"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, default=1, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), default="general", nullable=False)
    contact_name = Column(String(150), nullable=True)
    contact_info = Column(String(255), nullable=True)
    price = Column(DECIMAL(10, 2), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
