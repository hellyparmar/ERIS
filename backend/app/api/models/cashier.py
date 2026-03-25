"""
Cashier Authentication Model
4-digit PIN authentication for POS
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.api.db import Base
import bcrypt

class Cashier(Base):
    __tablename__ = "cashiers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    pin_hash = Column(String(255), nullable=False)  # bcrypt hash of 4-digit PIN
    role = Column(String(20), default="cashier")  # cashier or manager
    store_id = Column(Integer, nullable=False)  # FK to stores.id (UUID in Supabase)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def set_pin(self, pin: str):
        """Hash and store 4-digit PIN"""
        if not pin.isdigit() or len(pin) != 4:
            raise ValueError("PIN must be exactly 4 digits")
        self.pin_hash = bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()
    
    def verify_pin(self, pin: str) -> bool:
        """Verify PIN against stored hash"""
        return bcrypt.checkpw(pin.encode(), self.pin_hash.encode())
