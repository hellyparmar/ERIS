"""
Database model for storing integration tokens
"""

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from api.db.base import Base


class IntegrationToken(Base):
    """Store OAuth tokens for third-party integrations"""
    
    __tablename__ = "integration_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    integration_type = Column(String(50), nullable=False)  # 'zoho_books', 'odoo', etc.
    
    # Encrypted tokens
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    token_type = Column(String(50), default="Bearer")
    
    # Token metadata
    expires_at = Column(DateTime, nullable=False)
    scopes = Column(Text)  # Comma-separated list
    additional_data = Column(Text)  # JSON for any extra data (API domain, etc.)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<IntegrationToken {self.integration_type} for org {self.organization_id}>"
