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


if __name__ == "__main__":
    unittest.main()