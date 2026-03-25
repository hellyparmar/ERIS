"""
Pydantic schemas for Employee Management endpoints
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class EmployeeRole(str, Enum):
    MANAGER = "manager"
    CASHIER = "cashier"
    SALES_ASSOCIATE = "sales_associate"
    INVENTORY_STAFF = "inventory_staff"
    SECURITY = "security"
    CLEANER = "cleaner"
    OTHER = "other"


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    HALF_DAY = "half_day"
    LEAVE = "leave"
    HOLIDAY = "holiday"


class LeaveType(str, Enum):
    SICK = "sick"
    CASUAL = "casual"
    EARNED = "earned"
    UNPAID = "unpaid"
    MATERNITY = "maternity"
    PATERNITY = "paternity"


# ==================== EMPLOYEE ====================

class EmployeeCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    email: Optional[str] = None
    role: EmployeeRole = EmployeeRole.SALES_ASSOCIATE
    store_id: Optional[int] = None
    hire_date: Optional[date] = None
    salary: Optional[float] = None
    salary_type: Optional[str] = "monthly"
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    role: Optional[EmployeeRole] = None
    store_id: Optional[int] = None
    salary: Optional[float] = None
    salary_type: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    is_active: Optional[bool] = None


class EmployeeResponse(BaseModel):
    id: int
    employee_id: str
    name: str
    email: Optional[str]
    phone: str
    role: str
    store_id: Optional[int]
    hire_date: Optional[date]
    is_active: bool
    salary: Optional[float]
    salary_type: Optional[str]
    address: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== ATTENDANCE ====================

class ClockInRequest(BaseModel):
    employee_id: int
    notes: Optional[str] = None


class ClockOutRequest(BaseModel):
    employee_id: int
    notes: Optional[str] = None


class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    date: date
    status: str
    clock_in: Optional[datetime]
    clock_out: Optional[datetime]
    total_hours: Optional[float]
    overtime_hours: Optional[float]
    notes: Optional[str]

    class Config:
        from_attributes = True


class AttendanceMarkRequest(BaseModel):
    employee_id: int
    date: date
    status: AttendanceStatus
    notes: Optional[str] = None


# ==================== PERFORMANCE ====================

class PerformanceResponse(BaseModel):
    id: int
    employee_id: int
    month: int
    year: int
    total_sales_count: int
    total_sales_amount: float
    avg_transaction_value: float
    days_present: int
    days_absent: int
    avg_hours_per_day: float
    customer_rating: Optional[float]
    manager_rating: Optional[float]

    class Config:
        from_attributes = True


# ==================== LEAVE ====================

class LeaveRequestCreate(BaseModel):
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: Optional[str] = None


class LeaveApprovalRequest(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected)$")
    review_notes: Optional[str] = None


class LeaveResponse(BaseModel):
    id: int
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    total_days: int
    reason: Optional[str]
    status: str
    review_notes: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
