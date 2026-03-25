"""
test_models.py – Unit tests for SQLAlchemy database models.
Verifies that models can be instantiated, persisted, and
queried correctly against an in-memory SQLite database.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal


class TestEmployeeModel:
    """Tests for Employee and related models."""

    def test_create_employee(self, db):
        from api.db.employee_models import Employee, EmployeeRole
        emp = Employee(
            employee_id="EMP9001",
            name="Aisha Sharma",
            phone="9876543210",
            role=EmployeeRole.CASHIER,
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)
        assert emp.id is not None
        assert emp.name == "Aisha Sharma"
        assert emp.is_active is True

    def test_employee_default_fields(self, db):
        from api.db.employee_models import Employee, EmployeeRole
        emp = Employee(
            employee_id="EMP9002",
            name="Ravi Kumar",
            phone="9123456789",
            role=EmployeeRole.MANAGER,
        )
        db.add(emp)
        db.commit()
        assert emp.salary is None
        assert emp.salary_type == "monthly"

    def test_attendance_record(self, db):
        from api.db.employee_models import Employee, EmployeeRole, Attendance, AttendanceStatus
        emp = Employee(employee_id="EMP9003", name="Priya", phone="9000000001", role=EmployeeRole.CASHIER)
        db.add(emp)
        db.commit()

        att = Attendance(
            employee_id=emp.id,
            date=date.today(),
            status=AttendanceStatus.PRESENT,
            clock_in=datetime.now(),
        )
        db.add(att)
        db.commit()
        db.refresh(att)
        assert att.id is not None
        assert att.employee_id == emp.id
        assert att.status == AttendanceStatus.PRESENT

    def test_leave_request(self, db):
        from api.db.employee_models import Employee, EmployeeRole, LeaveRequest, LeaveType
        emp = Employee(employee_id="EMP9004", name="Dev", phone="9000000002", role=EmployeeRole.CASHIER)
        db.add(emp)
        db.commit()

        leave = LeaveRequest(
            employee_id=emp.id,
            leave_type=LeaveType.SICK,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 3),
            total_days=3,
            status="pending",
        )
        db.add(leave)
        db.commit()
        db.refresh(leave)
        assert leave.total_days == 3
        assert leave.status == "pending"


class TestSupplierModel:
    def test_create_supplier(self, db):
        from api.db.multitenant_models import Supplier
        import uuid
        s = Supplier(
            name="ABC Traders",
            phone="9001112222",
            payment_terms_days=30,
            organization_id=uuid.uuid4(),
        )
        db.add(s)
        db.commit()
        db.refresh(s)
        assert s.id is not None
        assert s.is_active is True

    def test_supplier_payment_terms_default(self, db):
        from api.db.multitenant_models import Supplier
        import uuid
        s = Supplier(name="XYZ Distributors", organization_id=uuid.uuid4())
        db.add(s)
        db.commit()
        assert s.payment_terms_days == 30


class TestProductModel:
    def test_create_product(self, db, sample_product):
        assert sample_product.id is not None
        assert sample_product.name == "Test Biscuit"
        assert float(sample_product.price) == 25.0

    def test_product_query(self, db, sample_product):
        from api.db.multitenant_models import Product
        product = db.query(Product).filter(Product.sku == "BIS-001").first()
        assert product is not None
        assert product.name == "Test Biscuit"

    def test_product_update(self, db, sample_product):
        sample_product.price = 30.0
        db.commit()
        db.refresh(sample_product)
        assert float(sample_product.price) == 30.0
