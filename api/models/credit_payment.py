"""
Enterprise Retail Intelligence System v3.0
Credit Payment Model - Track customer credit payments
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from api.db.models import Base


class CreditPayment(Base):
    """Credit payment model for tracking customer payments"""
    __tablename__ = 'credit_payments'
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, index=True)
    
    # Payment Details
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(20), nullable=False)  # cash, card, upi, bank_transfer
    reference_number = Column(String(50))  # Transaction ID, check number, etc.
    
    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(Integer)  # User ID who recorded the payment
    
    # Relationships
    # customer = relationship("Customer", back_populates="credit_payments")
    
    def __repr__(self):
        return f"<CreditPayment(id={self.id}, customer_id={self.customer_id}, amount={self.amount}, method='{self.payment_method}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'amount': float(self.amount) if self.amount else 0,
            'payment_method': self.payment_method,
            'reference_number': self.reference_number,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }
