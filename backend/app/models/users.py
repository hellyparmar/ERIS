"""
Simplified User model matching the current database schema.
"""

import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func, text, JSON
from sqlalchemy.orm import relationship
from .base import Base

class UserRoleEnum(str, enum.Enum):
    super_admin = "super_admin"
    area_manager = "area_manager"
    outlet_manager = "outlet_manager"

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_system_role = Column(Boolean, default=False)
    is_active = Column(Boolean, nullable=False, server_default=text('true'), default=True)
    is_deleted = Column(Boolean, nullable=False, server_default=text('false'), default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        if hasattr(other, 'value') and isinstance(other.value, str):
            return self.name == other.value
        if isinstance(other, Role):
            return self.id == other.id
        return NotImplemented

    def __ne__(self, other):
        equal = self.__eq__(other)
        if equal is NotImplemented:
            return NotImplemented
        return not equal

    def __str__(self):
        return self.name

class UserOutletAccess(Base):
    __tablename__ = "user_outlets"
    __table_args__ = {'extend_existing': True}

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    outlet_id = Column(Integer, ForeignKey("outlets.id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    user = relationship("User", back_populates="outlet_access")
    outlet = relationship("Outlet")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    email_verified = Column(Boolean, nullable=False, server_default=text('false'), default=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    dashboard_layout = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text('true'), default=True, index=True)
    is_deleted = Column(Boolean, nullable=False, server_default=text('false'), default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Deprecated: Keep for backward compatibility, use user_outlet_access instead
    outlet_id = Column(Integer, ForeignKey("outlets.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    role = relationship("Role", backref="users")
    organization = relationship("Organization", backref="users")
    outlet_access = relationship("UserOutletAccess", back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @full_name.setter
    def full_name(self, value):
        parts = value.split(" ", 1)
        self.first_name = parts[0]
        self.last_name = parts[1] if len(parts) > 1 else ""

    @property
    def hashed_password(self):
        """Compatibility alias for password_hash"""
        return self.password_hash

    @hashed_password.setter
    def hashed_password(self, value):
        """Compatibility alias for password_hash"""
        self.password_hash = value

    def __repr__(self):
        return f"<User {self.username}>"
