"""
Enterprise Retail Intelligence System v3.0
Loyalty Transaction Model - Track loyalty points earn/redeem/expire
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from api.db.models import Base


class LoyaltyTransaction(Base):
    """Loyalty transaction model for points tracking"""
    __tablename__ = 'loyalty_transactions'
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, index=True)
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=True)
    
    # Transaction Details
    transaction_type = Column(String(20), nullable=False)  # earn, redeem, expire, adjustment
    points = Column(Integer, nullable=False)  # Positive for earn, negative for redeem/expire
    balance_after = Column(Integer, nullable=False)
    
    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    # customer = relationship("Customer", back_populates="loyalty_transactions")
    
    def __repr__(self):
        return f"<LoyaltyTransaction(id={self.id}, customer_id={self.customer_id}, type='{self.transaction_type}', points={self.points})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'sale_id': self.sale_id,
            'transaction_type': self.transaction_type,
            'points': self.points,
            'balance_after': self.balance_after,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
