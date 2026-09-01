"""
Unit Tests for Outlet-Based Data Isolation

Tests the core data isolation mechanism that ensures:
- super_admin users can access data from all outlets
- area_manager users can access data from all assigned outlets
- outlet_manager users can only access data from their assigned outlet
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_isolation import OutletDataAccess, require_outlet_access
from app.models.users import UserRoleEnum, UserOutletAccess
from app.api.deps import get_accessible_outlet_ids, get_outlet_scope


class TestOutletDataAccess(unittest.TestCase):
    """Test the OutletDataAccess utility class"""

    def test_super_admin_user_has_all_access(self):
        """super_admin users should have access to all outlets"""
        user = Mock()
        user.role = UserRoleEnum.super_admin
        user.outlet_id = None
        user.outlet_access = []

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        self.assertIsNone(allowed_outlets)  # None means all outlets

    def test_area_manager_user_has_multiple_outlet_access(self):
        """area_manager users should have access to all assigned outlets"""
        user = Mock()
        user.role = UserRoleEnum.area_manager
        user.outlet_id = None
        
        access1 = Mock(spec=UserOutletAccess)
        access1.outlet_id = 5
        access2 = Mock(spec=UserOutletAccess)
        access2.outlet_id = 10
        user.outlet_access = [access1, access2]

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        self.assertEqual(allowed_outlets, [5, 10])

    def test_outlet_manager_user_has_single_outlet_access(self):
        """outlet_manager users should only have access to their assigned outlet"""
        user = Mock()
        user.role = UserRoleEnum.outlet_manager
        
        access = Mock(spec=UserOutletAccess)
        access.outlet_id = 3
        user.outlet_access = [access]
        user.outlet_id = 3

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        self.assertEqual(allowed_outlets, [3])

    def test_user_without_outlet_has_no_access(self):
        """Users without outlet assignment should have no access"""
        user = Mock()
        user.role = UserRoleEnum.outlet_manager
        user.outlet_id = None
        user.outlet_access = []

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        self.assertEqual(allowed_outlets, [])

    def test_super_admin_can_access_any_outlet(self):
        """super_admin users should be able to access any specific outlet"""
        user = Mock()
        user.role = UserRoleEnum.super_admin
        user.outlet_id = None
        user.outlet_access = []

        self.assertTrue(require_outlet_access(user, 1))
        self.assertTrue(require_outlet_access(user, 999))

    def test_outlet_manager_can_access_own_outlet_only(self):
        """outlet_manager users should only access their own outlet"""
        user = Mock()
        user.role = UserRoleEnum.outlet_manager
        user.outlet_id = 5
        
        access = Mock(spec=UserOutletAccess)
        access.outlet_id = 5
        user.outlet_access = [access]

        self.assertTrue(require_outlet_access(user, 5))
        self.assertFalse(require_outlet_access(user, 1))
        self.assertFalse(require_outlet_access(user, 999))

    def test_get_accessible_outlet_ids_dependency_admin(self):
        """Test the get_accessible_outlet_ids FastAPI dependency for super_admin"""
        admin_user = Mock()
        admin_user.role = UserRoleEnum.super_admin
        admin_user.is_active = True
        
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [(1,), (2,), (3,)]
        mock_db.execute.return_value = mock_result
        
        outlets = asyncio.run(get_accessible_outlet_ids(admin_user, mock_db))
        self.assertEqual(outlets, [1, 2, 3])

    def test_get_accessible_outlet_ids_dependency_manager(self):
        """Test the get_accessible_outlet_ids FastAPI dependency for area_manager / outlet_manager"""
        manager_user = Mock()
        manager_user.role = UserRoleEnum.area_manager
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
        outlet_user.role = UserRoleEnum.outlet_manager
        outlet_user.is_active = True
        outlet_user.outlet_access = []
        outlet_user.outlet_id = 9
        
        outlets = asyncio.run(get_accessible_outlet_ids(outlet_user, mock_db))
        self.assertEqual(outlets, [9])

    def test_sync_get_outlet_scope(self):
        """Test the synchronous get_outlet_scope helper"""
        mock_db = MagicMock()
        
        # super_admin
        admin_user = Mock()
        admin_user.role = Mock(name="role", value="super_admin")
        admin_user.role.name = "super_admin"
        o1 = Mock(id=1); o2 = Mock(id=2)
        mock_db.query.return_value.all.return_value = [o1, o2]
        self.assertEqual(get_outlet_scope(admin_user, mock_db), [1, 2])
        
        # outlet_manager with direct outlet_id
        mgr_user = Mock()
        mgr_user.role = Mock(name="role", value="outlet_manager")
        mgr_user.role.name = "outlet_manager"
        mgr_user.id = 101
        mgr_user.outlet_id = 1
        mock_db.query.return_value.filter.return_value.all.return_value = []
        self.assertEqual(get_outlet_scope(mgr_user, mock_db), [1])

    def test_cross_outlet_manager_isolation(self):
        """
        Concrete assertion that outlet_manager A assigned to Outlet 1 CANNOT
        access Outlet 2, and outlet_manager B assigned to Outlet 2 CANNOT access Outlet 1.
        """
        outlet_1_id = 10
        outlet_2_id = 20

        # Manager A -> Outlet 1
        manager_a = Mock()
        manager_a.id = 1
        manager_a.role = UserRoleEnum.outlet_manager
        manager_a.outlet_id = outlet_1_id
        acc_a = Mock(spec=UserOutletAccess)
        acc_a.outlet_id = outlet_1_id
        manager_a.outlet_access = [acc_a]

        # Manager B -> Outlet 2
        manager_b = Mock()
        manager_b.id = 2
        manager_b.role = UserRoleEnum.outlet_manager
        manager_b.outlet_id = outlet_2_id
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


if __name__ == "__main__":
    unittest.main()