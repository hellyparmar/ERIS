import enum
from sqlalchemy import Column, Integer, String, Enum, Text, DateTime, func, JSON
from .base import Base

class MessageChannel(str, enum.Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String(200), index=True)
    sender_type = Column(String(50))
    sender_id = Column(Integer)
    recipient_type = Column(String(50))
    recipient_id = Column(Integer)
    channel = Column(Enum(MessageChannel), default=MessageChannel.IN_APP)
    subject = Column(String(200))
    body = Column(Text)
    related_entity_type = Column(String(50), nullable=True)
    related_entity_id = Column(Integer, nullable=True)
    attachments = Column(JSON, nullable=True)
    status = Column(String(50), default="sent")
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
