"""
Employees Management API Router
"""

from datetime import datetime, timedelta
from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_, and_, select
from uuid import UUID

from app.database import get_db
from app.models import User, Outlet, Employee
from app.api.deps import get_current_active_user
from app.core.data_isolation import OutletDataAccess
from app.api.schemas.employee import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse,
    EmployeeListResponse, AttendanceSummary
)

router = APIRouter(prefix="/api/v1/employees", tags=["employees"])


def check_manager_permission(current_user: User):
    """Verify user is manager or superadmin"""
    if current_user.role not in ["super_admin", "outlet_manager", "area_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can perform this action"
        )


@router.get("/", response_model=EmployeeListResponse)
async def list_employees(
    outlet_id: Optional[UUID] = None,
    shift: Optional[str] = None,
    role: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List employees with filtering.
    Superadmin sees all, manager sees their outlet only.
    """
    allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(current_user, db)
    if not allowed_outlet_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No outlets accessible"
        )

    # Build query
    stmt = select(Employee).where(Employee.outlet_id.in_(allowed_outlet_ids))

    # Apply filters
    if outlet_id:
        if outlet_id not in allowed_outlet_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this outlet"
            )
        stmt = stmt.where(Employee.outlet_id == outlet_id)

    if shift:
        stmt = stmt.where(Employee.shift == shift)

    if role:
        stmt = stmt.where(Employee.role.ilike(f"%{role}%"))

    if search:
        stmt = stmt.where(
            or_(
                Employee.name.ilike(f"%{search}%"),
                Employee.email.ilike(f"%{search}%"),
                Employee.phone.ilike(f"%{search}%")
            )
        )

    if is_active is not None:
        stmt = stmt.where(Employee.is_active == is_active)

    # Get total count
    count_stmt = select(func.count()).select_from(Employee).where(Employee.outlet_id.in_(allowed_outlet_ids))
    if outlet_id:
        count_stmt = count_stmt.where(Employee.outlet_id == outlet_id)
    if shift:
        count_stmt = count_stmt.where(Employee.shift == shift)
    if role:
        count_stmt = count_stmt.where(Employee.role.ilike(f"%{role}%"))
    if search:
        count_stmt = count_stmt.where(
            or_(
                Employee.name.ilike(f"%{search}%"),
                Employee.email.ilike(f"%{search}%"),
                Employee.phone.ilike(f"%{search}%")
            )
        )
    if is_active is not None:
        count_stmt = count_stmt.where(Employee.is_active == is_active)

    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()
    total_pages = (total + per_page - 1) // per_page

    # Apply pagination
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    employees = result.scalars().all()

    return EmployeeListResponse(
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        items=[EmployeeResponse.from_orm(emp) for emp in employees]
    )


@router.post("/", response_model=EmployeeResponse)
async def create_employee(
    employee_data: EmployeeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create new employee.
    Manager can create for their outlet only. Superadmin can create for any outlet.
    """
    check_manager_permission(current_user)

    # Check outlet access
    if not OutletDataAccess.can_access_outlet(employee_data.outlet_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this outlet"
        )

    # Check if outlet exists
    result = await db.execute(select(Outlet).where(Outlet.outlet_id == employee_data.outlet_id))
    query = result.scalar_one_or_none()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")

    # Check for duplicate email
    result = await db.execute(select(Employee).where(Employee.email == employee_data.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Employee with this email already exists")

    # Create employee
    employee = Employee(
        outlet_id=employee_data.outlet_id,
        name=employee_data.name,
        email=employee_data.email,
        phone=employee_data.phone,
        role=employee_data.role,
        salary=employee_data.salary,
        joining_date=employee_data.joining_date,
        shift=employee_data.shift
    )

    db.add(employee)
    db.commit()
    db.refresh(employee)

    return EmployeeResponse.from_orm(employee)


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get single employee details"""
    result = await db.execute(select(Employee).where(Employee.employee_id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Check outlet access
    if not OutletDataAccess.can_access_outlet(employee.outlet_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this employee"
        )

    return EmployeeResponse.from_orm(employee)


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: UUID,
    employee_data: EmployeeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update employee details. Same role restrictions as create."""
    check_manager_permission(current_user)

    result = await db.execute(select(Employee).where(Employee.employee_id == employee_id))

    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Check outlet access
    if not OutletDataAccess.can_access_outlet(employee.outlet_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this employee"
        )

    # Check for duplicate email if email is being updated
    if employee_data.email and employee_data.email != employee.email:
        result = await db.execute(select(Employee).where(Employee.email == employee_data.email))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Employee with this email already exists")

    # Update fields
    update_data = employee_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)

    employee.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(employee)

    return EmployeeResponse.from_orm(employee)


@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Soft delete employee (set is_active=false). Superadmin only."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmin can delete employees"
        )

    result = await db.execute(select(Employee).where(Employee.employee_id == employee_id))

    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee.is_active = False
    employee.updated_at = datetime.utcnow()

    db.commit()

    return {
        "employee_id": employee_id,
        "message": "Employee deactivated successfully"
    }


@router.get("/outlet/{outlet_id}/attendance-summary", response_model=AttendanceSummary)
async def get_attendance_summary(
    outlet_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Returns shift distribution stats for an outlet.
    """
    if not OutletDataAccess.can_access_outlet(outlet_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this outlet"
        )

    # Get employee stats
    result = await db.execute(
        select(Employee).where(
            Employee.outlet_id == outlet_id,
            Employee.is_active == True
        )
    )
    employees = result.scalars().all()
    total_employees = len(employees)
    active_employees = total_employees  # All queried are active

    # Shift distribution
    shift_counts = {}
    for emp in employees:
        shift = emp.shift.value if hasattr(emp.shift, 'value') else str(emp.shift)
        shift_counts[shift] = shift_counts.get(shift, 0) + 1

    # Role distribution
    role_counts = {}
    for emp in employees:
        role_counts[emp.role] = role_counts.get(emp.role, 0) + 1

    # Mock attendance rate (would need attendance tracking table)
    attendance_rate = 0.85  # Placeholder

    return AttendanceSummary(
        shift_distribution=shift_counts,
        role_distribution=role_counts,
        attendance_rate=attendance_rate,
        total_employees=total_employees,
        active_employees=active_employees
    )
