"""
users.py - RBAC User, Role, Permission Models
MSc Data Science Project - Enterprise Retail Intelligence System
"""

import enum
import uuid
from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey,
    DateTime, Table, UniqueConstraint, Index, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Uuid

from .base import Base


# ── Enumerations ──────────────────────────────────────────────────────────────

class UserRoleEnum(enum.Enum):
    ADMIN   = "admin"
    MANAGER = "manager"
    STAFF   = "staff"


# ── Association table: Role ↔ Permission (many-to-many) ───────────────────────

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id",       Integer, ForeignKey("roles.id",       ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


# ── Permission ─────────────────────────────────────────────────────────────────

class Permission(Base):
    """
    Granular action-based permission.
    Examples: 'inventory:read', 'sales:create', 'reports:export'
    """
    __tablename__ = "permissions"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), unique=True, nullable=False, index=True)
    resource    = Column(String(50),  nullable=False)   # e.g. 'inventory'
    action      = Column(String(50),  nullable=False)   # e.g. 'read'
    description = Column(Text)

    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

    def __repr__(self):
        return f"<Permission {self.name}>"


# ── Role ───────────────────────────────────────────────────────────────────────

class Role(Base):
    """
    User role that bundles a set of permissions.
    Pre-seeded with: admin, manager, staff
    """
    __tablename__ = "roles"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100))
    description = Column(Text)
    is_system   = Column(Boolean, default=True)   # system roles cannot be deleted

    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users       = relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role {self.name}>"


# ── User ───────────────────────────────────────────────────────────────────────

class User(Base):
    """
    System user with RBAC.
    Belongs to one Organization; may be assigned to one or more Stores.
    """
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Credentials
    username        = Column(String(100), nullable=False, index=True)
    email           = Column(String(255), nullable=False, index=True)
    password_hash   = Column(String(255), nullable=False)

    # RBAC
    role_id         = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)

    # Profile
    full_name       = Column(String(255))
    phone           = Column(String(20))
    avatar_url      = Column(String(500))

    # Status
    is_active       = Column(Boolean, default=True, index=True)
    is_superadmin   = Column(Boolean, default=False)
    last_login_at   = Column(DateTime(timezone=True))
    failed_logins   = Column(Integer, default=0)
    locked_until    = Column(DateTime(timezone=True))

    # Timestamps
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at      = Column(DateTime(timezone=True))    # soft-delete

    # Relationships
    role            = relationship("Role", back_populates="users")
    organization    = relationship("Organization", back_populates="users")
    outlets         = relationship("UserStore", back_populates="user")

    # Indexes
    __table_args__ = (
        UniqueConstraint("organization_id", "username", name="uq_user_org_username"),
        UniqueConstraint("organization_id", "email",    name="uq_user_org_email"),
        Index("idx_users_role",         "role_id"),
        Index("idx_users_org_active",   "organization_id", "is_active"),
    )

    def __repr__(self):
        return f"<User {self.username} ({self.email})>"


# ── UserStore (junction: User ↔ Store) ─────────────────────────────────────────

class UserStore(Base):
    """
    Assigns users to one or more stores, enabling multi-outlet staff.
    """
    __tablename__ = "user_stores"

    id       = Column(Integer, primary_key=True, index=True)
    user_id  = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id = Column(Uuid(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    is_primary = Column(Boolean, default=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user  = relationship("User",  back_populates="outlets")
    store = relationship("Store", back_populates="staff")

    __table_args__ = (
        UniqueConstraint("user_id", "store_id", name="uq_user_store"),
    )
