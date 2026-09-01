"""
Pydantic schemas for Employee Management endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum
from uuid import UUID


class EmployeeRole(str, Enum):
    MANAGER = "manager"
    CASHIER = "cashier"
    SALES_ASSOCIATE = "sales_associate"
    INVENTORY_STAFF = "inventory_staff"
    SECURITY = "security"
    CLEANER = "cleaner"
    OTHER = "other"


class EmployeeShift(str, Enum):
    MORNING = "morning"
    EVENING = "evening"
    NIGHT = "night"


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
    outlet_id: UUID = Field(..., description="Outlet ID where employee works")
    name: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., min_length=10, max_length=20)
    role: str = Field(..., min_length=2, max_length=100)
    salary: float = Field(..., gt=0)
    joining_date: date
    shift: EmployeeShift = EmployeeShift.MORNING


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    salary: Optional[float] = None
    shift: Optional[EmployeeShift] = None
    is_active: Optional[bool] = None


class EmployeeResponse(BaseModel):
    employee_id: UUID
    outlet_id: UUID
    name: str
    phone: str
    role: str
    salary: float
    joining_date: date
    shift: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmployeeListResponse(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    items: List[EmployeeResponse]


class AttendanceSummary(BaseModel):
    shift_distribution: dict
    role_distribution: dict
    attendance_rate: float
    total_employees: int
    active_employees: int


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


class ClockInRequest(BaseModel):
    employee_id: int
    notes: Optional[str] = None


class ClockOutRequest(BaseModel):
    employee_id: int
    notes: Optional[str] = None
