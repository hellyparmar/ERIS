"""
Employee Management Service
Business logic for staff profiles, attendance tracking, and performance KPIs
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.employee_models import (
    Employee, Attendance, PerformanceMetric, LeaveRequest,
    EmployeeRole, AttendanceStatus
)
from app.services.base_service import OutletIsolatedService
from app.models.users import User


class EmployeeService(OutletIsolatedService):
    def __init__(self, db: Session, current_user: Optional[User] = None):
        super().__init__(db, current_user)

    # ==================== EMPLOYEE CRUD ====================

    def _generate_employee_id(self) -> str:
        """Generate a unique sequential employee ID like EMP001"""
        last = self.db.query(Employee).order_by(Employee.id.desc()).first()
        seq = (last.id + 1) if last else 1
        return f"EMP{seq:04d}"

    def create_employee(self, data: dict) -> Employee:
        store_id = data.get("store_id")
        if store_id is not None:
            self.validate_outlet_access(store_id)
        emp = Employee(
            employee_id=self._generate_employee_id(),
            name=data["name"],
            phone=data["phone"],
            email=data.get("email"),
            role=EmployeeRole[data.get("role", "SALES_ASSOCIATE").upper()],
            store_id=store_id,
            hire_date=data.get("hire_date", date.today()),
            salary=Decimal(str(data["salary"])) if data.get("salary") else None,
            salary_type=data.get("salary_type", "monthly"),
            address=data.get("address"),
            emergency_contact_name=data.get("emergency_contact_name"),
            emergency_contact_phone=data.get("emergency_contact_phone"),
        )
        self.db.add(emp)
        self.db.commit()
        self.db.refresh(emp)
        return emp

    def get_employee(self, employee_id: int) -> Optional[Employee]:
        emp = self.db.query(Employee).filter(
            Employee.id == employee_id,
            Employee.is_active == True
        ).first()
        if emp and emp.store_id is not None:
            self.validate_outlet_access(emp.store_id)
        return emp

    def list_employees(
        self,
        store_id: Optional[int] = None,
        role: Optional[str] = None,
        is_active: bool = True,
        page: int = 1,
        limit: int = 20
    ) -> dict:
        query = self.db.query(Employee).filter(Employee.is_active == is_active)
        query = self.apply_outlet_filter(query, outlet_column='store_id')
        if store_id:
            self.validate_outlet_access(store_id)
            query = query.filter(Employee.store_id == store_id)
        if role:
            query = query.filter(Employee.role == EmployeeRole[role.upper()])

        total = query.count()
        employees = query.order_by(Employee.name).offset((page - 1) * limit).limit(limit).all()
        return {"items": [e.to_dict() for e in employees], "total": total, "page": page}

    def update_employee(self, employee_id: int, data: dict) -> Optional[Employee]:
        emp = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not emp:
            return None
        if emp.store_id is not None:
            self.validate_outlet_access(emp.store_id)
        if "store_id" in data and data["store_id"] is not None:
            self.validate_outlet_access(data["store_id"])

        field_map = {
            "name", "phone", "email", "store_id", "salary",
            "salary_type", "address", "emergency_contact_name",
            "emergency_contact_phone", "is_active"
        }
        for key in field_map:
            if key in data and data[key] is not None:
                if key == "salary":
                    setattr(emp, key, Decimal(str(data[key])))
                elif key == "role":
                    setattr(emp, key, EmployeeRole[data[key].upper()])
                else:
                    setattr(emp, key, data[key])
        if "role" in data and data["role"]:
            emp.role = EmployeeRole[data["role"].upper()]

        self.db.commit()
        self.db.refresh(emp)
        return emp

    def delete_employee(self, employee_id: int) -> bool:
        emp = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not emp:
            return False
        if emp.store_id is not None:
            self.validate_outlet_access(emp.store_id)
        emp.is_active = False
        self.db.commit()
        return True

    # ==================== ATTENDANCE ====================

    def clock_in(self, employee_id: int, notes: Optional[str] = None) -> Attendance:
        today = date.today()
        now = datetime.now()

        # Check if already clocked in today
        existing = self.db.query(Attendance).filter(
            Attendance.employee_id == employee_id,
            Attendance.date == today
        ).first()

        if existing:
            if existing.clock_in and not existing.clock_out:
                raise ValueError("Employee is already clocked in. Please clock out first.")
            elif existing.clock_in and existing.clock_out:
                raise ValueError("Employee has already completed attendance for today.")
            existing.clock_in = now
            existing.status = AttendanceStatus.PRESENT
            existing.notes = notes
            self.db.commit()
            self.db.refresh(existing)
            return existing

        record = Attendance(
            employee_id=employee_id,
            date=today,
            status=AttendanceStatus.PRESENT,
            clock_in=now,
            notes=notes
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def clock_out(self, employee_id: int, notes: Optional[str] = None) -> Attendance:
        today = date.today()
        now = datetime.now()

        record = self.db.query(Attendance).filter(
            Attendance.employee_id == employee_id,
            Attendance.date == today
        ).first()

        if not record or not record.clock_in:
            raise ValueError("No clock-in record found for today. Please clock in first.")
        if record.clock_out:
            raise ValueError("Employee has already clocked out today.")

        record.clock_out = now

        # Calculate hours worked
        duration = now - record.clock_in
        total_hours = duration.total_seconds() / 3600
        record.total_hours = round(total_hours, 2)

        # Mark overtime if > 8 hours
        if total_hours > 8:
            record.overtime_hours = round(total_hours - 8, 2)

        # Mark half-day if < 4 hours
        if total_hours < 4:
            record.status = AttendanceStatus.HALF_DAY

        if notes:
            record.notes = notes

        self.db.commit()
        self.db.refresh(record)
        return record

    def get_attendance(
        self,
        employee_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        store_id: Optional[int] = None,
        limit: int = 100
    ) -> List[dict]:
        query = self.db.query(Attendance).join(Employee, Employee.id == Attendance.employee_id)
        query = self.apply_outlet_filter(query, outlet_column='store_id')

        if employee_id:
            query = query.filter(Attendance.employee_id == employee_id)
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        if store_id:
            self.validate_outlet_access(store_id)
            query = query.filter(Employee.store_id == store_id)

        records = query.order_by(Attendance.date.desc()).limit(limit).all()
        return [r.to_dict() for r in records]

    def mark_attendance(self, employee_id: int, att_date: date, status: str, notes: str = None) -> Attendance:
        emp = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if emp and emp.store_id is not None:
            self.validate_outlet_access(emp.store_id)

        existing = self.db.query(Attendance).filter(
            Attendance.employee_id == employee_id,
            Attendance.date == att_date
        ).first()

        att_status = AttendanceStatus[status.upper()]

        if existing:
            existing.status = att_status
            if notes:
                existing.notes = notes
            self.db.commit()
            self.db.refresh(existing)
            return existing

        record = Attendance(
            employee_id=employee_id,
            date=att_date,
            status=att_status,
            notes=notes
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def today_status(self, store_id: Optional[int] = None) -> List[dict]:
        """Get a summary of all employee attendance statuses for today."""
        today = date.today()
        query = self.db.query(Employee).filter(Employee.is_active == True)
        query = self.apply_outlet_filter(query, outlet_column='store_id')
        if store_id:
            self.validate_outlet_access(store_id)
            query = query.filter(Employee.store_id == store_id)
        employees = query.all()

        result = []
        for emp in employees:
            att = self.db.query(Attendance).filter(
                Attendance.employee_id == emp.id,
                Attendance.date == today
            ).first()

            result.append({
                "employee_id": emp.id,
                "employee_code": emp.employee_id,
                "name": emp.name,
                "role": emp.role.value if emp.role else None,
                "status": att.status.value if att else "not_recorded",
                "clock_in": att.clock_in.isoformat() if att and att.clock_in else None,
                "clock_out": att.clock_out.isoformat() if att and att.clock_out else None,
                "total_hours": att.total_hours if att else None,
            })
        return result

    # ==================== PERFORMANCE ====================

    def calculate_performance(
        self,
        employee_id: int,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> dict:
        """Calculate or retrieve performance metrics for an employee for a given month."""
        today = date.today()
        month = month or today.month
        year = year or today.year

        emp = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not emp:
            raise ValueError(f"Employee {employee_id} not found")
        if emp.store_id is not None:
            self.validate_outlet_access(emp.store_id)

        # Attendance data for the month
        start = date(year, month, 1)
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        end = date(year, month, last_day)

        att_records = self.db.query(Attendance).filter(
            Attendance.employee_id == employee_id,
            Attendance.date >= start,
            Attendance.date <= end
        ).all()

        days_present = sum(1 for a in att_records if a.status == AttendanceStatus.PRESENT)
        days_absent = sum(1 for a in att_records if a.status == AttendanceStatus.ABSENT)
        hours_list = [a.total_hours for a in att_records if a.total_hours]
        avg_hours = round(sum(hours_list) / len(hours_list), 2) if hours_list else 0.0

        # Sales data — try to join on employee_id field in sales
        try:
            from app.models import Sale
            from sqlalchemy import extract
            sales = self.db.query(Sale).filter(
                Sale.employee_id == employee_id,
                extract("month", Sale.transaction_date) == month,
                extract("year", Sale.transaction_date) == year
            ).all()
            sales_count = len(sales)
            sales_amount = sum(float(s.total_amount) for s in sales)
            avg_txn = round(sales_amount / sales_count, 2) if sales_count else 0.0
        except Exception:
            sales_count = 0
            sales_amount = 0.0
            avg_txn = 0.0

        # Upsert PerformanceMetric
        metric = self.db.query(PerformanceMetric).filter(
            PerformanceMetric.employee_id == employee_id,
            PerformanceMetric.month == month,
            PerformanceMetric.year == year
        ).first()

        if not metric:
            metric = PerformanceMetric(employee_id=employee_id, month=month, year=year)
            self.db.add(metric)

        metric.total_sales_count = sales_count
        metric.total_sales_amount = Decimal(str(sales_amount))
        metric.avg_transaction_value = Decimal(str(avg_txn))
        metric.days_present = days_present
        metric.days_absent = days_absent
        metric.avg_hours_per_day = avg_hours

        self.db.commit()
        self.db.refresh(metric)
        return metric.to_dict()

    def get_all_performance(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None,
        store_id: Optional[int] = None
    ) -> List[dict]:
        today = date.today()
        month = month or today.month
        year = year or today.year

        emp_query = self.db.query(Employee).filter(Employee.is_active == True)
        emp_query = self.apply_outlet_filter(emp_query, outlet_column='store_id')
        if store_id:
            self.validate_outlet_access(store_id)
            emp_query = emp_query.filter(Employee.store_id == store_id)
        employees = emp_query.all()

        results = []
        for emp in employees:
            try:
                metric = self.calculate_performance(emp.id, month, year)
                metric["employee_name"] = emp.name
                metric["employee_code"] = emp.employee_id
                metric["role"] = emp.role.value if emp.role else None
                results.append(metric)
            except Exception:
                pass
        return results

    # ==================== LEAVE ====================

    def request_leave(self, data: dict) -> LeaveRequest:
        from app.models.employee_models import LeaveType
        start = data["start_date"]
        end = data["end_date"]
        total_days = (end - start).days + 1

        leave = LeaveRequest(
            employee_id=data["employee_id"],
            leave_type=LeaveType[data["leave_type"].upper()],
            start_date=start,
            end_date=end,
            total_days=total_days,
            reason=data.get("reason"),
            status="pending"
        )
        self.db.add(leave)
        self.db.commit()
        self.db.refresh(leave)
        return leave

    def review_leave(self, leave_id: int, status: str, reviewer_id: int, notes: str = None) -> LeaveRequest:
        leave = self.db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
        if not leave:
            raise ValueError(f"Leave request {leave_id} not found")
        leave.status = status
        leave.reviewed_by = reviewer_id
        leave.reviewed_at = datetime.now()
        leave.review_notes = notes
        self.db.commit()
        self.db.refresh(leave)
        return leave

    def get_leave_requests(self, employee_id: Optional[int] = None, status: Optional[str] = None) -> List[dict]:
        query = self.db.query(LeaveRequest)
        if employee_id:
            query = query.filter(LeaveRequest.employee_id == employee_id)
        if status:
            query = query.filter(LeaveRequest.status == status)
        return [r.to_dict() for r in query.order_by(LeaveRequest.created_at.desc()).all()]
