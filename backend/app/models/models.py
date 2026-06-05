"""
SQLAlchemy ORM Models for Enterprise Retail Intelligence System

This file defines all database models using SQLAlchemy 2.0 declarative syntax.
All models use UUID primary keys with PostgreSQL server-side defaults.
Timestamps are automatically managed with server defaults.
"""

from sqlalchemy import (
    Column, String, Integer, Float, Date, DateTime, Boolean, Text,
    ForeignKey, Enum, UniqueConstraint, Index, ARRAY, JSON, UUID,
    func, text
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List, Optional
import enum


from app.models.base import Base
from .sale import Sale


# Enums
class UserRole(enum.Enum):
    superadmin = "superadmin"
    manager = "manager"
    staff = "staff"


class AlertType(enum.Enum):
    low_stock = "low_stock"
    high_stock = "high_stock"
    sales_drop = "sales_drop"
    forecast_deviation = "forecast_deviation"


class AlertStatus(enum.Enum):
    active = "active"
    resolved = "resolved"
    snoozed = "snoozed"


class ContactType(enum.Enum):
    supplier = "supplier"
    distributor = "distributor"
    logistics = "logistics"


class InvoiceStatus(enum.Enum):
    paid = "paid"
    pending = "pending"
    overdue = "overdue"


class EmployeeShift(enum.Enum):
    morning = "morning"
    evening = "evening"
    night = "night"


class ForecastType(enum.Enum):
    sales = "sales"
    inventory = "inventory"


class MessageRole(enum.Enum):
    user = "user"
    assistant = "assistant"


# Models










class SalesFactor(Base):
    __tablename__ = "sales_factors"

    factor_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    outlet_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("outlets.outlet_id"),
        nullable=False
    )
    factor_date: Mapped[Date] = mapped_column(Date, nullable=False)
    is_holiday: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_weekend: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    temperature_celsius: Mapped[Optional[float]] = mapped_column(Float)
    rainfall_mm: Mapped[Optional[float]] = mapped_column(Float)
    festival_name: Mapped[Optional[str]] = mapped_column(String(255))
    local_event: Mapped[Optional[str]] = mapped_column(String(255))
    economic_index: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    outlet: Mapped["Outlet"] = relationship("Outlet", back_populates="sales_factors")

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint("outlet_id", "factor_date", name="uq_sales_factor_date"),
        Index("idx_sales_factors_outlet_id", "outlet_id"),
        Index("idx_sales_factors_factor_date", "factor_date"),
    )




class BusinessContact(Base):
    __tablename__ = "business_contacts"

    contact_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_person: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    gst_number: Mapped[Optional[str]] = mapped_column(String(15))
    address: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_type: Mapped[ContactType] = mapped_column(Enum(ContactType), nullable=False)
    product_categories: Mapped[List[str]] = mapped_column(ARRAY(String).with_variant(JSON, "sqlite"), default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="contact")

    # Indexes
    __table_args__ = (
        Index("idx_business_contacts_email", "email"),
        Index("idx_business_contacts_contact_type", "contact_type"),
        Index("idx_business_contacts_is_active", "is_active"),
    )




class Employee(Base):
    __tablename__ = "employees"

    employee_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    outlet_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("outlets.outlet_id"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    salary: Mapped[float] = mapped_column(Float, nullable=False)
    joining_date: Mapped[Date] = mapped_column(Date, nullable=False)
    shift: Mapped[EmployeeShift] = mapped_column(Enum(EmployeeShift), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    outlet: Mapped["Outlet"] = relationship("Outlet", back_populates="employees")

    # Indexes
    __table_args__ = (
        Index("idx_employees_outlet_id", "outlet_id"),
        Index("idx_employees_email", "email"),
        Index("idx_employees_shift", "shift"),
        Index("idx_employees_is_active", "is_active"),
    )


