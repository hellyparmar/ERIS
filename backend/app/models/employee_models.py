"""
Employee Management Database Models
Handles staff profiles, attendance tracking, and performance metrics
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Text, Enum, Date, Numeric
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import enum


class EmployeeRole(enum.Enum):
    MANAGER = "manager"
    CASHIER = "cashier"
    SALES_ASSOCIATE = "sales_associate"
    INVENTORY_STAFF = "inventory_staff"
    SECURITY = "security"
    CLEANER = "cleaner"
    OTHER = "other"


class AttendanceStatus(enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    HALF_DAY = "half_day"
    LEAVE = "leave"
    HOLIDAY = "holiday"


class LeaveType(enum.Enum):
    SICK = "sick"
    CASUAL = "casual"
    EARNED = "earned"
    UNPAID = "unpaid"
    MATERNITY = "maternity"
    PATERNITY = "paternity"


class Employee(Base):
    """Staff / Employee Profile"""
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    outlet_id = Column(Integer, ForeignKey("outlets.id", ondelete="CASCADE"), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(120), nullable=True)
    phone = Column(String(20), nullable=True)
    
    position = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    employment_type = Column(String(50), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    
    joining_date = Column(Date, nullable=False)
    exit_date = Column(Date, nullable=True)
    base_salary = Column(Numeric(10, 2), nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    attendance_records = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")
    performance_metrics = relationship("PerformanceMetric", back_populates="employee", cascade="all, delete-orphan")
    leave_requests = relationship("LeaveRequest", back_populates="employee", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "name": self.name,
            "phone": self.phone,
            "role": self.role.value if self.role else None,
            "outlet_id": self.outlet_id,
            "hire_date": self.hire_date.isoformat() if self.hire_date else None,
            "is_active": self.is_active,
            "salary": float(self.salary) if self.salary else None,
            "salary_type": self.salary_type,
            "address": self.address,
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Attendance(Base):
    """Daily attendance and time tracking"""
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    
    date = Column(Date, nullable=False, index=True)
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.PRESENT)
    
    clock_in = Column(DateTime(timezone=True), nullable=True)
    clock_out = Column(DateTime(timezone=True), nullable=True)
    
    # Duration in minutes
    total_hours = Column(Float, nullable=True)
    overtime_hours = Column(Float, default=0.0)
    
    notes = Column(Text, nullable=True)
    recorded_by = Column(Integer, nullable=True)  # Admin/Manager user ID
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="attendance_records")

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "date": self.date.isoformat() if self.date else None,
            "status": self.status.value if self.status else None,
            "clock_in": self.clock_in.isoformat() if self.clock_in else None,
            "clock_out": self.clock_out.isoformat() if self.clock_out else None,
            "total_hours": self.total_hours,
            "overtime_hours": self.overtime_hours,
            "notes": self.notes,
        }


class PerformanceMetric(Base):
    """Monthly performance KPIs per employee"""
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    
    # Period
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    
    # Sales KPIs
    total_sales_count = Column(Integer, default=0)
    total_sales_amount = Column(Numeric(14, 2), default=0.0)
    avg_transaction_value = Column(Numeric(10, 2), default=0.0)
    
    # Attendance KPIs
    days_present = Column(Integer, default=0)
    days_absent = Column(Integer, default=0)
    avg_hours_per_day = Column(Float, default=0.0)
    
    # Qualitative
    customer_rating = Column(Float, nullable=True)  # 1-5 scale
    manager_rating = Column(Float, nullable=True)   # 1-5 scale
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="performance_metrics")

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "month": self.month,
            "year": self.year,
            "total_sales_count": self.total_sales_count,
            "total_sales_amount": float(self.total_sales_amount) if self.total_sales_amount else 0.0,
            "avg_transaction_value": float(self.avg_transaction_value) if self.avg_transaction_value else 0.0,
            "days_present": self.days_present,
            "days_absent": self.days_absent,
            "avg_hours_per_day": self.avg_hours_per_day,
            "customer_rating": self.customer_rating,
            "manager_rating": self.manager_rating,
        }


class LeaveRequest(Base):
    """Employee leave requests and approvals"""
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    
    leave_type = Column(Enum(LeaveType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_days = Column(Integer, nullable=False)
    
    reason = Column(Text, nullable=True)
    
    # Approval workflow
    status = Column(String(20), default="pending")  # pending, approved, rejected
    reviewed_by = Column(Integer, nullable=True)  # Manager user ID
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="leave_requests")

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "leave_type": self.leave_type.value if self.leave_type else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "total_days": self.total_days,
            "reason": self.reason,
            "status": self.status,
            "review_notes": self.review_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
