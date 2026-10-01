"""
Unit Tests for Outlet-Based Data Isolation

Tests the core data isolation mechanism that ensures:
- admin users can access data from all outlets
- manager users can access assigned outlets
- viewer users can only read data from assigned outlets
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_isolation import OutletDataAccess, require_outlet_access
from app.models.users import UserRoleEnum, UserOutletAccess
from app.api.deps import get_accessible_outlet_ids, get_outlet_scope


class TestOutletDataAccess(unittest.TestCase):
    """Test the OutletDataAccess utility class"""

    def test_admin_user_has_all_access(self):
        """Admin users should have access to all outlets."""
        user = Mock()
        user.role = UserRoleEnum.admin
        user.outlet_access = []

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        self.assertIsNone(allowed_outlets)  # None means all outlets

    def test_manager_user_has_multiple_outlet_access(self):
        """Managers should have access to all assigned outlets."""
        user = Mock()
        user.role = UserRoleEnum.manager

        access1 = Mock(spec=UserOutletAccess)
        access1.outlet_id = 5
        access2 = Mock(spec=UserOutletAccess)
        access2.outlet_id = 10
        user.outlet_access = [access1, access2]

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        self.assertEqual(allowed_outlets, [5, 10])

    def test_viewer_user_has_single_outlet_access(self):
        """Viewers should only have access to their assigned outlet."""
        user = Mock()
        user.role = UserRoleEnum.viewer

        access = Mock(spec=UserOutletAccess)
        access.outlet_id = 3
        user.outlet_access = [access]

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        self.assertEqual(allowed_outlets, [3])

    def test_user_without_outlet_has_no_access(self):
        """Users without outlet assignment should have no access"""
        user = Mock()
        user.role = UserRoleEnum.manager
        user.outlet_access = []

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        self.assertEqual(allowed_outlets, [])

    def test_admin_can_access_any_outlet(self):
        """Admins should be able to access any specific outlet."""
        user = Mock()
        user.role = UserRoleEnum.admin
        user.outlet_access = []

        self.assertTrue(require_outlet_access(user, 1))
        self.assertTrue(require_outlet_access(user, 999))

    def test_manager_can_access_own_outlet_only(self):
        """Managers should only access their assigned outlets."""
        user = Mock()
        user.role = UserRoleEnum.manager

        access = Mock(spec=UserOutletAccess)
        access.outlet_id = 5
        user.outlet_access = [access]

        self.assertTrue(require_outlet_access(user, 5))
        self.assertFalse(require_outlet_access(user, 1))
        self.assertFalse(require_outlet_access(user, 999))

    def test_get_accessible_outlet_ids_dependency_admin(self):
        """Test the get_accessible_outlet_ids FastAPI dependency for admin."""
        admin_user = Mock()
        admin_user.role = UserRoleEnum.admin
        admin_user.is_active = True

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [(1,), (2,), (3,)]
        mock_db.execute.return_value = mock_result

        outlets = asyncio.run(get_accessible_outlet_ids(admin_user, mock_db))
        self.assertEqual(outlets, [1, 2, 3])

    def test_get_accessible_outlet_ids_dependency_manager(self):
        """Test the dependency for manager and viewer outlet assignments."""
        manager_user = Mock()
        manager_user.role = UserRoleEnum.manager
        manager_user.is_active = True
        access1 = Mock(spec=UserOutletAccess)
        access1.outlet_id = 4
        access2 = Mock(spec=UserOutletAccess)
        access2.outlet_id = 7
        manager_user.outlet_access = [access1, access2]

        mock_db = AsyncMock(spec=AsyncSession)

        outlets = asyncio.run(get_accessible_outlet_ids(manager_user, mock_db))
        self.assertEqual(outlets, [4, 7])

        outlet_user = Mock()
        outlet_user.role = UserRoleEnum.viewer
        outlet_user.is_active = True
        outlet_access = Mock(spec=UserOutletAccess)
        outlet_access.outlet_id = 9
        outlet_user.outlet_access = [outlet_access]

        outlets = asyncio.run(get_accessible_outlet_ids(outlet_user, mock_db))
        self.assertEqual(outlets, [9])

    def test_sync_get_outlet_scope(self):
        """Test the synchronous get_outlet_scope helper"""
        mock_db = MagicMock()

        # Admin
        admin_user = Mock()
        admin_user.role = Mock(name="role", value="admin")
        admin_user.role.name = "admin"
        admin_user.organization_id = 1
        o1 = Mock(id=1)
        o2 = Mock(id=2)
        mock_db.query.return_value.filter.return_value.all.return_value = [o1, o2]
        self.assertEqual(get_outlet_scope(admin_user, mock_db), [1, 2])

        # Manager with an outlet assignment
        mgr_user = Mock()
        mgr_user.role = Mock(name="role", value="manager")
        mgr_user.role.name = "manager"
        mgr_user.id = 101
        mock_db.query.return_value.filter.return_value.all.return_value = [Mock(outlet_id=1)]
        self.assertEqual(get_outlet_scope(mgr_user, mock_db), [1])

    def test_cross_outlet_manager_assignment_isolation(self):
        """
        Concrete assertion that Manager A assigned to Outlet 1 cannot access
        Outlet 2, and Manager B assigned to Outlet 2 cannot access Outlet 1.
        """
        outlet_1_id = 10
        outlet_2_id = 20

        # Manager A -> Outlet 1
        manager_a = Mock()
        manager_a.id = 1
        manager_a.role = UserRoleEnum.manager
        acc_a = Mock(spec=UserOutletAccess)
        acc_a.outlet_id = outlet_1_id
        manager_a.outlet_access = [acc_a]

        # Manager B -> Outlet 2
        manager_b = Mock()
        manager_b.id = 2
        manager_b.role = UserRoleEnum.manager
        acc_b = Mock(spec=UserOutletAccess)
        acc_b.outlet_id = outlet_2_id
        manager_b.outlet_access = [acc_b]

        # 1. require_outlet_access check
        self.assertTrue(require_outlet_access(manager_a, outlet_1_id))
        self.assertFalse(require_outlet_access(manager_a, outlet_2_id))

        self.assertTrue(require_outlet_access(manager_b, outlet_2_id))
        self.assertFalse(require_outlet_access(manager_b, outlet_1_id))

        # 2. OutletDataAccess allowed IDs check
        allowed_a = OutletDataAccess.get_allowed_outlet_ids(manager_a)
        allowed_b = OutletDataAccess.get_allowed_outlet_ids(manager_b)

        self.assertEqual(allowed_a, [outlet_1_id])
        self.assertEqual(allowed_b, [outlet_2_id])
        self.assertNotIn(outlet_2_id, allowed_a)
        self.assertNotIn(outlet_1_id, allowed_b)


from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_active_user, get_current_user, get_db
from app.database import get_db_sync_dependency

client = TestClient(app)


class TestRouterDataIsolation(unittest.TestCase):
    def setUp(self):
        self.outlet_1_id = 10
        self.outlet_2_id = 20

        self.manager_a = Mock()
        self.manager_a.id = 1
        self.manager_a.role = UserRoleEnum.manager
        acc_a = Mock(spec=UserOutletAccess)
        acc_a.outlet_id = self.outlet_1_id
        self.manager_a.outlet_access = [acc_a]

        self.manager_b = Mock()
        self.manager_b.id = 2
        self.manager_b.role = UserRoleEnum.manager
        acc_b = Mock(spec=UserOutletAccess)
        acc_b.outlet_id = self.outlet_2_id
        self.manager_b.outlet_access = [acc_b]

    def _override_user(self, user_mock):
        app.dependency_overrides[get_current_active_user] = lambda: user_mock
        app.dependency_overrides[get_current_user] = lambda: user_mock

        class DualMock(MagicMock):
            def __await__(self):
                async def _coro():
                    return self

                return _coro().__await__()

        mock_res = DualMock()
        mock_res.all.return_value = []
        mock_res.fetchall.return_value = []
        mock_res.scalars.return_value.all.return_value = []
        mock_res.scalar.return_value = 0
        mock_res.scalar_one_or_none.return_value = MagicMock(id=user_mock.outlet_access[0].outlet_id)
        mock_res.first.return_value = None
        mock_db = MagicMock()
        mock_db.execute.return_value = mock_res
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_db_sync_dependency] = lambda: mock_db

        async def mock_accessible_outlets(user=None, db=None):
            return [acc.outlet_id for acc in user_mock.outlet_access] if user_mock.outlet_access else []

        app.dependency_overrides[get_accessible_outlet_ids] = mock_accessible_outlets
        app.dependency_overrides[get_outlet_scope] = lambda: [acc.outlet_id for acc in user_mock.outlet_access]

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_sales_router_isolation(self):
        self._override_user(self.manager_a)
        res = client.get(f"/api/v1/sales/?outlet_id={self.outlet_2_id}")
        self.assertEqual(res.status_code, 403)

        res = client.get(f"/api/v1/sales/?outlet_id={self.outlet_1_id}")
        self.assertNotEqual(res.status_code, 403)

    @patch("app.routers.forecasting.run_job")
    def test_forecasting_router_isolation(self, mock_run_job):
        self._override_user(self.manager_a)
        res = client.post(f"/api/v1/forecasting/sales?outlet_id={self.outlet_2_id}")
        self.assertEqual(res.status_code, 403)

        res = client.post(f"/api/v1/forecasting/sales?outlet_id={self.outlet_1_id}")
        self.assertNotEqual(res.status_code, 403)

    def test_employees_router_isolation(self):
        """Employee management is deferred and must not be exposed."""
        self._override_user(self.manager_a)
        res = client.get(f"/api/v1/employees/?store_id={self.outlet_2_id}")
        self.assertEqual(res.status_code, 404)

    def test_outlets_router_isolation(self):
        self._override_user(self.manager_a)
        res = client.get(f"/api/v1/outlets/{self.outlet_2_id}")
        self.assertEqual(res.status_code, 403)

        res = client.get(f"/api/v1/outlets/{self.outlet_1_id}")
        self.assertNotEqual(res.status_code, 403)


if __name__ == "__main__":
    unittest.main()
