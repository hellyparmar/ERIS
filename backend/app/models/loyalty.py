from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.models.base import Base

class LoyaltyAccount(Base):
    """Customer Loyalty Account tracking points and tiers"""
    __tablename__ = "loyalty_accounts"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    points_balance = Column(Integer, default=0, nullable=False)
    tier = Column(String(50), default="bronze", nullable=False)
    lifetime_points = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", backref="loyalty_account")
    points_history = relationship("LoyaltyPoints", back_populates="account", cascade="all, delete-orphan")
    bonuses = relationship("LoyaltyBonus", back_populates="account", cascade="all, delete-orphan")


class LoyaltyPoints(Base):
    """Ledger of points earned, redeemed, or expired"""
    __tablename__ = "loyalty_points"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, index=True)
    account_id = Column(BigInteger, ForeignKey("loyalty_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    points = Column(Integer, nullable=False)
    transaction_type = Column(String(50), nullable=False)  # 'earned', 'redeemed', 'expired', 'adjusted'
    reference_id = Column(String(100), nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    account = relationship("LoyaltyAccount", back_populates="points_history")


class LoyaltyBonus(Base):
    """Promotional or milestone bonus points for customer loyalty"""
    __tablename__ = "loyalty_bonuses"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, index=True)
    account_id = Column(BigInteger, ForeignKey("loyalty_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    bonus_points = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    is_claimed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    account = relationship("LoyaltyAccount", back_populates="bonuses")
