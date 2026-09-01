import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, func, Text
from sqlalchemy.orm import relationship
from .base import Base

class NotificationTypeEnum(str, enum.Enum):
    low_stock = "low_stock"
    day_close_reminder = "day_close_reminder"
    new_alert = "new_alert"
    system = "system"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    outlet_id = Column(Integer, ForeignKey("outlets.id", ondelete="SET NULL"), nullable=True, index=True)
    type = Column(Enum(NotificationTypeEnum), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    link = Column(String(255), nullable=True)

    # Relationships
    user = relationship("User", backref="notifications")
    outlet = relationship("Outlet")
