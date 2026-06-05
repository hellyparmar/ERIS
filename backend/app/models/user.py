"""
User Models
"""

from sqlalchemy import String, Boolean, ForeignKey, Enum, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid
from app.models.base import Base
import enum
import uuid

class UserRole(str, enum.Enum):
    super_admin = "super_admin"
    area_manager = "area_manager"
    outlet_manager = "outlet_manager"
    staff = "staff"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    outlet_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("outlets.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)