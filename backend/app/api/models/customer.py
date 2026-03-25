"""
Enterprise Retail Intelligence System v3.0
Customer Model - Customer profiles with loyalty and credit tracking
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.api.db.models import Base


class Customer(Base):
    """Customer model with loyalty and credit management"""
    __tablename__ = 'customers'
    __table_args__ = {'extend_existing': True}
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    name = Column(String(100), nullable=False)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    email = Column(String(100))
    address = Column(Text)
    
    # Segmentation
    segment = Column(String(20), default='New', index=True)  # VIP, Regular, New
    lifetime_value = Column(Numeric(10, 2), default=0)
    total_purchases = Column(Integer, default=0)
    
    # Loyalty
    loyalty_points = Column(Integer, default=0)
    loyalty_tier = Column(String(20), default='Bronze', index=True)  # Bronze, Silver, Gold, Platinum
    
    # Credit
    credit_limit = Column(Numeric(10, 2), default=0)
    outstanding_balance = Column(Numeric(10, 2), default=0)
    
    # Timestamps
    first_purchase_at = Column(DateTime)
    last_purchase_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # loyalty_transactions = relationship("LoyaltyTransaction", back_populates="customer")
    # credit_payments = relationship("CreditPayment", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', phone='{self.phone}', tier='{self.loyalty_tier}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'segment': self.segment,
            'lifetime_value': float(self.lifetime_value) if self.lifetime_value else 0,
            'total_purchases': self.total_purchases,
            'loyalty_points': self.loyalty_points,
            'loyalty_tier': self.loyalty_tier,
            'credit_limit': float(self.credit_limit) if self.credit_limit else 0,
            'outstanding_balance': float(self.outstanding_balance) if self.outstanding_balance else 0,
            'first_purchase_at': self.first_purchase_at.isoformat() if self.first_purchase_at else None,
            'last_purchase_at': self.last_purchase_at.isoformat() if self.last_purchase_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
