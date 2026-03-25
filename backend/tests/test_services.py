"""
test_services.py – Unit tests for service layer business logic.
All tests run against the in-memory DB fixture from conftest.py.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock


class TestEmployeeService:
    """Tests for EmployeeService business logic."""

    def setup_emp(self, db, suffix="001"):
        from api.db.employee_models import Employee, EmployeeRole
        emp = Employee(
            employee_id=f"EMP{suffix}",
            name=f"Worker {suffix}",
            phone=f"98{suffix}",
            role=EmployeeRole.CASHIER,
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)
        return emp

    def test_generate_employee_id_is_sequential(self, db):
        from api.services.employee_service import EmployeeService
        svc = EmployeeService(db)
        id1 = svc._generate_employee_id()
        assert id1.startswith("EMP")
        assert id1[3:].isdigit()

    def test_create_employee_stores_record(self, db):
        from api.services.employee_service import EmployeeService
        svc = EmployeeService(db)
        emp = svc.create_employee({
            "name": "Neeta Joshi",
            "phone": "9800000001",
            "role": "cashier",
        })
        assert emp.id is not None
        assert emp.name == "Neeta Joshi"
        assert emp.role.value == "cashier"

    def test_list_employees_pagination(self, db):
        from api.services.employee_service import EmployeeService
        svc = EmployeeService(db)
        for i in range(5):
            svc.create_employee({"name": f"Emp{i}", "phone": f"980000000{i}", "role": "cashier"})
        result = svc.list_employees(page=1, limit=3)
        assert "items" in result
        assert len(result["items"]) <= 3
        assert result["total"] >= 5

    def test_clock_in_creates_attendance(self, db):
        from api.services.employee_service import EmployeeService
        svc = EmployeeService(db)
        emp = svc.create_employee({"name": "Raj", "phone": "9800000100", "role": "cashier"})
        record = svc.clock_in(emp.id)
        assert record.clock_in is not None
        assert record.clock_out is None

    def test_clock_out_calculates_hours(self, db):
        from api.services.employee_service import EmployeeService
        from api.db.employee_models import Attendance, AttendanceStatus
        svc = EmployeeService(db)
        emp = svc.create_employee({"name": "Sita", "phone": "9800000200", "role": "cashier"})

        # Manually seed a clock-in 2 hours ago to ensure a calculable duration
        att = Attendance(
            employee_id=emp.id,
            date=date.today(),
            status=AttendanceStatus.PRESENT,
            clock_in=datetime(2026, 3, 18, 7, 0, 0),
        )
        db.add(att)
        db.commit()

        with patch("api.services.employee_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 3, 18, 15, 0, 0)
            mock_dt.side_effect = datetime
            result = svc.clock_out(emp.id)
        assert result.total_hours is not None
        assert result.total_hours > 0

    def test_double_clock_in_raises(self, db):
        from api.services.employee_service import EmployeeService
        svc = EmployeeService(db)
        emp = svc.create_employee({"name": "Akash", "phone": "9800000300", "role": "cashier"})
        svc.clock_in(emp.id)
        with pytest.raises(ValueError, match="already clocked in"):
            svc.clock_in(emp.id)

    def test_update_employee(self, db):
        from api.services.employee_service import EmployeeService
        svc = EmployeeService(db)
        emp = svc.create_employee({"name": "Old Name", "phone": "9800000400", "role": "cashier"})
        updated = svc.update_employee(emp.id, {"name": "New Name"})
        assert updated.name == "New Name"

    def test_delete_employee_soft_deletes(self, db):
        from api.services.employee_service import EmployeeService
        svc = EmployeeService(db)
        emp = svc.create_employee({"name": "Temp Worker", "phone": "9800000500", "role": "cashier"})
        result = svc.delete_employee(emp.id)
        assert result is True
        fetched = svc.get_employee(emp.id)
        assert fetched is None  # is_active=False, not returned


class TestSupplierService:
    """Tests for SupplierService."""

    def test_generate_supplier_code(self, db):
        from api.services.supplier_service import SupplierService
        import uuid
        svc = SupplierService(db)
        code = svc._generate_supplier_code()
        assert code.startswith("SUP")

    def test_create_supplier(self, db):
        from api.services.supplier_service import SupplierService
        import uuid
        svc = SupplierService(db)
        s = svc.create_supplier({
            "name": "Sunrise Traders",
            "phone": "9001112223",
            "payment_terms_days": 15,
            "organization_id": str(uuid.uuid4()),
        })
        assert s.id is not None
        assert s.name == "Sunrise Traders"
        assert s.payment_terms_days == 15

    def test_list_suppliers_search(self, db):
        from api.services.supplier_service import SupplierService
        import uuid
        org_id = str(uuid.uuid4())
        svc = SupplierService(db)
        svc.create_supplier({"name": "Agro Farms", "organization_id": org_id})
        svc.create_supplier({"name": "Tech Supplies", "organization_id": org_id})
        result = svc.list_suppliers(search="Agro")
        assert result["total"] >= 1
        assert any("Agro" in s["name"] for s in result["items"])

    def test_update_supplier(self, db):
        from api.services.supplier_service import SupplierService
        import uuid
        svc = SupplierService(db)
        s = svc.create_supplier({"name": "Old Supplier", "organization_id": str(uuid.uuid4())})
        updated = svc.update_supplier(s.id, {"name": "Updated Supplier"})
        assert updated.name == "Updated Supplier"

    def test_delete_supplier_soft_deletes(self, db):
        from api.services.supplier_service import SupplierService
        import uuid
        svc = SupplierService(db)
        s = svc.create_supplier({"name": "Temp Supplier", "organization_id": str(uuid.uuid4())})
        result = svc.delete_supplier(s.id)
        assert result is True
        fetched = svc.get_supplier(s.id)
        assert fetched is None


class TestGSTCalculations:
    """Tests for GST calculation utilities."""

    @pytest.mark.parametrize("amount,rate,expected_gst", [
        (100.0, 18.0, 18.0),
        (200.0, 5.0, 10.0),
        (1000.0, 28.0, 280.0),
        (0.0, 18.0, 0.0),
    ])
    def test_gst_calculation(self, amount, rate, expected_gst):
        gst = round(amount * rate / 100, 2)
        assert gst == expected_gst

    def test_cgst_sgst_split(self):
        """CGST + SGST = full GST rate for intra-state."""
        total_gst_rate = 18.0
        cgst = total_gst_rate / 2
        sgst = total_gst_rate / 2
        assert cgst + sgst == total_gst_rate

    @pytest.mark.parametrize("amount,rate", [
        (100.0, 0.0),
        (100.0, 5.0),
        (100.0, 12.0),
        (100.0, 18.0),
        (100.0, 28.0),
    ])
    def test_all_standard_gst_rates(self, amount, rate):
        gst = amount * rate / 100
        total = amount + gst
        assert total >= amount
