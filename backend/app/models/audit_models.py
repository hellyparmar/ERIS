"""
Database Audit Models
Tracks sensitive actions and changes across the application
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
# Using standard String/Text for UUID if not using Postgres, but since main model uses sqlalchemy.types.Uuid,
# we will use the same for compatibility.
from sqlalchemy.types import Uuid
import uuid
from . import Base

class AuditLog(Base):
    """
    Audit Log table to track sensitive actions 
    (e.g., changes to user roles, large transactions, config changes)
    """
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # What happened
    action = Column(String(100), nullable=False, index=True) # e.g., 'UPDATE_ROLE', 'DELETE_INVOICE'
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(String(255), nullable=False) # String to support both Int and UUID PKs
    
    # Who did it
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    
    # Old vs New state (JSON)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # Context
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # When it happened
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AuditLog {self.action} on {self.table_name}:{self.record_id}>"
