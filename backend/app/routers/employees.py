"""
Employee Management Router
REST API for staff profiles, attendance tracking, and performance KPIs
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.database import get_db_sync_dependency as get_db
from app.api.deps import get_current_active_user
from app.models.users import User
from app.services.employee_service import EmployeeService
from app.schemas.employee import (
    EmployeeCreate, EmployeeUpdate, ClockInRequest, ClockOutRequest, AttendanceMarkRequest,
    LeaveRequestCreate, LeaveApprovalRequest
)
from app.services.audit_service import log_audit_action_sync

router = APIRouter(prefix="/employees", tags=["employees"])


# ==================== EMPLOYEE CRUD ====================

@router.post("/", status_code=201)
async def create_employee(
    data: EmployeeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new employee profile"""
    try:
        svc = EmployeeService(db, current_user)
        emp = svc.create_employee(data.dict())
        log_audit_action_sync(
            db=db,
            action="create_employee",
            performed_by=current_user.id,
            context={"employee_id": emp.employee_id, "name": emp.name}
        )
        return {"success": True, "data": emp.to_dict(), "message": "Employee created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_employees(
    store_id: Optional[int] = Query(None),
    role: Optional[str] = Query(None),
    is_active: bool = Query(True),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all employees with optional filters"""
    try:
        svc = EmployeeService(db, current_user)
        return svc.list_employees(store_id=store_id, role=role, is_active=is_active, page=page, limit=limit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/today-status")
async def today_attendance_status(
    store_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get today's attendance status for all employees"""
    try:
        svc = EmployeeService(db, current_user)
        return {"success": True, "data": svc.today_status(store_id=store_id)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_all_performance(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None),
    store_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get performance KPIs for all employees for a given month"""
    try:
        svc = EmployeeService(db, current_user)
        return {"success": True, "data": svc.get_all_performance(month=month, year=year, store_id=store_id)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attendance")
async def get_attendance(
    employee_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    store_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get attendance records with filters"""
    try:
        svc = EmployeeService(db, current_user)
        records = svc.get_attendance(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            store_id=store_id,
            limit=limit
        )
        return {"success": True, "data": records}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leave")
async def get_leave_requests(
    employee_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get leave requests"""
    try:
        svc = EmployeeService(db, current_user)
        return {"success": True, "data": svc.get_leave_requests(employee_id=employee_id, status=status)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CLOCK IN/OUT ====================

@router.post("/clock-in", status_code=201)
async def clock_in(
    request: ClockInRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Clock in an employee for today"""
    try:
        svc = EmployeeService(db, current_user)
        record = svc.clock_in(request.employee_id, request.notes)
        return {"success": True, "data": record.to_dict(), "message": "Clocked in successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clock-out")
async def clock_out(
    request: ClockOutRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Clock out an employee for today"""
    try:
        svc = EmployeeService(db, current_user)
        record = svc.clock_out(request.employee_id, request.notes)
        return {
            "success": True,
            "data": record.to_dict(),
            "message": f"Clocked out successfully. Total hours: {record.total_hours:.2f}h"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-attendance")
async def mark_attendance(
    request: AttendanceMarkRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Manually mark attendance for an employee"""
    try:
        svc = EmployeeService(db, current_user)
        record = svc.mark_attendance(
            request.employee_id, request.date, request.status.value, request.notes
        )
        return {"success": True, "data": record.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== LEAVE ====================

@router.post("/leave", status_code=201)
async def request_leave(
    request: LeaveRequestCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit a leave request"""
    try:
        svc = EmployeeService(db, current_user)
        leave = svc.request_leave(request.dict())
        return {"success": True, "data": leave.to_dict(), "message": "Leave request submitted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/leave/{leave_id}/review")
async def review_leave(
    leave_id: int,
    approval: LeaveApprovalRequest,
    reviewer_id: int = Query(1),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Approve or reject a leave request"""
    try:
        svc = EmployeeService(db, current_user)
        leave = svc.review_leave(leave_id, approval.status, reviewer_id, approval.review_notes)
        return {"success": True, "data": leave.to_dict(), "message": f"Leave request {approval.status}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INDIVIDUAL EMPLOYEE ====================

@router.get("/{employee_id}")
async def get_employee(
    employee_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get employee profile details"""
    try:
        svc = EmployeeService(db, current_user)
        emp = svc.get_employee(employee_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        return {"success": True, "data": emp.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{employee_id}")
async def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update employee profile"""
    try:
        svc = EmployeeService(db, current_user)
        emp = svc.update_employee(employee_id, data.dict(exclude_unset=True))
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        return {"success": True, "data": emp.to_dict(), "message": "Employee updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Deactivate an employee (soft delete)"""
    try:
        svc = EmployeeService(db, current_user)
        success = svc.delete_employee(employee_id)
        if not success:
            raise HTTPException(status_code=404, detail="Employee not found")
        return {"success": True, "message": "Employee deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{employee_id}/performance")
async def get_employee_performance(
    employee_id: int,
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get performance metrics for a specific employee"""
    try:
        svc = EmployeeService(db, current_user)
        data = svc.calculate_performance(employee_id, month, year)
        return {"success": True, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{employee_id}/attendance")
async def get_employee_attendance(
    employee_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get attendance history for a specific employee"""
    try:
        svc = EmployeeService(db, current_user)
        records = svc.get_attendance(employee_id=employee_id, start_date=start_date, end_date=end_date)
        return {"success": True, "data": records}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
