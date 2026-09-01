"""
PRODUCTION DATABASE SCHEMA
Enterprise Retail Intelligence System - Complete SQLAlchemy Models
MSc Data Science Project

This file contains all database models with proper relationships,
validation, and constraints for PostgreSQL.
"""

from enum import Enum

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, Date, Enum as SQLEnum, Table, UniqueConstraint, Index,
    func
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import UUID

import logging

logger = logging.getLogger(__name__)

from .base import Base

# ═══════════════════════════════════════════════════════════════════════════
# ENUMERATIONS
# ═══════════════════════════════════════════════════════════════════════════

class UserRoleEnum(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"


class PermissionTypeEnum(str, Enum):
    """Permission type enumeration"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE_USERS = "manage_users"
    VIEW_ALL_OUTLETS = "view_all_outlets"
    EXPORT_REPORTS = "export_reports"
    MANAGE_SETTINGS = "manage_settings"


class PaymentMethodEnum(str, Enum):
    """Payment method enumeration"""
    CASH = "cash"
    CARD = "card"
    UPI = "upi"
    CHEQUE = "cheque"
    BANK_TRANSFER = "bank_transfer"
    WALLET = "wallet"


class PaymentStatusEnum(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIAL = "partial"


class SaleStatusEnum(str, Enum):
    """Sale status enumeration"""
    INITIATED = "initiated"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class AlertTypeEnum(str, Enum):
    """Alert type enumeration"""
    LOW_STOCK = "low_stock"
    OVERSTOCKED = "overstocked"
    ANOMALY = "anomaly"
    FORECAST_WARNING = "forecast_warning"
    EXPIRY_WARNING = "expiry_warning"
    SALES_ALERT = "sales_alert"


class AlertSeverityEnum(str, Enum):
    """Alert severity level"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class InventoryMovementTypeEnum(str, Enum):
    """Inventory movement type"""
    IN = "in"
    OUT = "out"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    DAMAGE = "damage"


class AttendanceStatusEnum(str, Enum):
    """Employee attendance status"""
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    HALF_DAY = "half_day"
    LEAVE = "leave"


# ═══════════════════════════════════════════════════════════════════════════
# ASSOCIATION TABLES (Many-to-Many)
# ═══════════════════════════════════════════════════════════════════════════

user_outlets = Table(
    'user_outlets',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('outlet_id', Integer, ForeignKey('outlets.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_user_outlets', 'user_id', 'outlet_id'),
    extend_existing=True
)

# ═══════════════════════════════════════════════════════════════════════════
# 1. USER MANAGEMENT & RBAC
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# 2. BUSINESS ENTITIES
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# 3. INVENTORY MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

class Category(Base):
    """
    Product category model
    """
    __tablename__ = 'categories'
    __table_args__ = (
        UniqueConstraint('name', 'organization_id', name='uq_category_name_org'),
        Index('idx_category_organization_id', 'organization_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    code = Column(String(50), nullable=True)
    
    # Hierarchy
    parent_category_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    organization = relationship('Organization')
    # products = relationship('Product', back_populates='category')
    parent = relationship('Category', remote_side=[id], backref='subcategories')

    def __repr__(self):
        return f"<Category {self.name}>"


class StockLevel(Base):
    """
    Stock level at each outlet
    """
    __tablename__ = 'stock_levels'
    __table_args__ = (
        UniqueConstraint('product_id', 'outlet_id', name='uq_stock_product_outlet'),
        Index('idx_stock_product_id', 'product_id'),
        Index('idx_stock_outlet_id', 'outlet_id'),
        Index('idx_stock_low_stock', 'is_low_stock'),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    outlet_id = Column(Integer, ForeignKey('outlets.id', ondelete='CASCADE'), nullable=False)
    
    quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)  # For pending orders
    available_quantity = Column(Integer, default=0, nullable=False)  # = quantity - reserved
    
    # Thresholds
    minimum_level = Column(Integer, default=10, nullable=False)
    maximum_level = Column(Integer, nullable=True)
    
    # Flags
    is_low_stock = Column(Boolean, default=False, nullable=False)
    last_restocked = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    product = relationship('Product')
    outlet = relationship('Outlet')

    def __repr__(self):
        return f"<StockLevel {self.product_id} @ outlet {self.outlet_id}>"


class InventoryMovement(Base):
    """
    Inventory movement tracking (in/out/adjustment)
    """
    __tablename__ = 'inventory_movements'
    __table_args__ = (
        Index('idx_movement_product_id', 'product_id'),
        Index('idx_movement_outlet_id', 'outlet_id'),
        Index('idx_movement_type', 'movement_type'),
        Index('idx_movement_date', 'movement_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    outlet_id = Column(Integer, ForeignKey('outlets.id', ondelete='CASCADE'), nullable=False)
    
    # Movement details
    movement_type = Column(SQLEnum(InventoryMovementTypeEnum), nullable=False)
    quantity = Column(Integer, nullable=False)
    reference_number = Column(String(100), nullable=True)  # PO number, Invoice number, etc.
    
    # Additional info
    reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Dates
    movement_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    product = relationship('Product')

    def __repr__(self):
        return f"<InventoryMovement {self.product_id} - {self.movement_type}>"


# ═══════════════════════════════════════════════════════════════════════════
# 4. SALES & INVOICING
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# 5. ALERTS & NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# 6. FORECASTING (FOR ML MODELS)
# ═══════════════════════════════════════════════════════════════════════════

class ForecastModel(Base):
    """
    Forecast model metadata (stores information about ML models)
    """
    __tablename__ = 'forecast_models'
    __table_args__ = (
        Index('idx_forecast_model_outlet_id', 'outlet_id'),
        Index('idx_forecast_model_product_id', 'product_id'),
        Index('idx_forecast_model_is_active', 'is_active'),
    )

    id = Column(Integer, primary_key=True, index=True)
    outlet_id = Column(Integer, ForeignKey('outlets.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    
    # Model details
    model_name = Column(String(200), nullable=False)
    model_type = Column(String(100), nullable=False)  # e.g., PROPHET, LSTM, ARIMA
    description = Column(Text, nullable=True)
    
    # Model parameters
    parameters = Column(Text, nullable=True)  # JSON serialized
    
    # Performance metrics
    mae = Column(Float, nullable=True)  # Mean Absolute Error
    mape = Column(Float, nullable=True)  # Mean Absolute Percentage Error
    rmse = Column(Float, nullable=True)  # Root Mean Square Error
    r_squared = Column(Float, nullable=True)
    
    # Training details
    training_start_date = Column(Date, nullable=True)
    training_end_date = Column(Date, nullable=True)
    last_trained = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    outlet = relationship('Outlet')
    product = relationship('Product')
    # predictions = relationship('ForecastResult', back_populates='model', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<ForecastModel {self.model_name}>"


