"""
Unit Tests for Outlet-Based Data Isolation

Tests the core data isolation mechanism that ensures:
- Admin users can access data from all outlets
- Manager users can only access data from their assigned outlet
- Users cannot access data from outlets they don't have permission for
"""

import pytest
from unittest.mock import Mock

from app.core.data_isolation import OutletDataAccess
from app.models.users import UserRoleEnum


class TestOutletDataAccess:
    """Test the OutletDataAccess utility class"""

    def test_admin_user_has_all_access(self):
        """Admin users should have access to all outlets"""
        user = Mock()
        user.role = UserRoleEnum.ADMIN
        user.outlet_id = 1

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        assert allowed_outlets is None  # None means all outlets

    def test_manager_user_has_outlet_access(self):
        """Manager users should only have access to their assigned outlet"""
        user = Mock()
        user.role = UserRoleEnum.MANAGER
        user.outlet_id = 5

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        assert allowed_outlets == [5]

    def test_staff_user_has_outlet_access(self):
        """Staff users should only have access to their assigned outlet"""
        user = Mock()
        user.role = UserRoleEnum.STAFF
        user.outlet_id = 3

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        assert allowed_outlets == [3]

    def test_user_without_outlet_has_no_access(self):
        """Users without outlet assignment should have no access"""
        user = Mock()
        user.role = "outlet_manager"
        user.outlet_id = None

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        assert allowed_outlets == []

    def test_admin_can_access_any_outlet(self):
        """Admin users should be able to access any specific outlet"""
        from app.core.data_isolation import require_outlet_access

        user = Mock()
        user.role = UserRoleEnum.ADMIN
        user.outlet_id = 1

        assert require_outlet_access(user, 1) == True
        assert require_outlet_access(user, 999) == True

    def test_manager_can_access_own_outlet_only(self):
        """Manager users should only access their own outlet"""
        from app.core.data_isolation import require_outlet_access

        user = Mock()
        user.role = UserRoleEnum.MANAGER
        user.outlet_id = 5

        assert require_outlet_access(user, 5) == True
        assert require_outlet_access(user, 1) == False
        assert require_outlet_access(user, 999) == False

    def test_manager_without_outlet_cannot_access_any(self):
        """Manager without outlet assignment cannot access any outlets"""
        from app.core.data_isolation import require_outlet_access

        user = Mock()
        user.role = UserRoleEnum.MANAGER
        user.outlet_id = None

        assert require_outlet_access(user, 1) == False
        assert require_outlet_access(user, 5) == False


class TestSecurityVulnerabilities:
    """Test that security vulnerabilities are prevented"""

    def test_manager_cannot_access_other_outlet_via_parameter(self):
        """Manager should not be able to access other outlets even with direct parameters"""
        from app.core.data_isolation import require_outlet_access

        user = Mock()
        user.role = UserRoleEnum.MANAGER
        user.outlet_id = 1

        # Even if frontend sends outlet_id=2, user should not have access
        assert require_outlet_access(user, 1) == True   # Own outlet
        assert require_outlet_access(user, 2) == False  # Other outlet
        assert require_outlet_access(user, 999) == False  # Non-existent outlet

    def test_staff_cannot_access_admin_data(self):
        """Staff users should not have admin-level access"""
        user = Mock()
        user.role = UserRoleEnum.STAFF
        user.outlet_id = 3

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        assert allowed_outlets == [3]  # Only their outlet
        assert allowed_outlets is not None  # Not admin access

    def test_empty_outlet_list_blocks_all_access(self):
        """Users with empty outlet list should be blocked from all data"""
        user = Mock()
        user.role = UserRoleEnum.MANAGER
        user.outlet_id = None

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        assert allowed_outlets == []

        # Should not be able to access any outlet
        from app.core.data_isolation import require_outlet_access
        assert require_outlet_access(user, 1) == False
        assert require_outlet_access(user, 100) == False


class TestOutletFilteringLogic:
    """Test the outlet filtering logic"""

    def test_admin_gets_no_filter(self):
        """Admin users should get no outlet filtering"""
        user = Mock()
        user.role = UserRoleEnum.ADMIN

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        assert allowed_outlets is None  # No filtering

    def test_manager_gets_outlet_filter(self):
        """Manager users should get outlet filtering"""
        user = Mock()
        user.role = UserRoleEnum.MANAGER
        user.outlet_id = 7

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        assert allowed_outlets == [7]

    def test_staff_gets_outlet_filter(self):
        """Staff users should get outlet filtering"""
        user = Mock()
        user.role = UserRoleEnum.STAFF
        user.outlet_id = 2

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        assert allowed_outlets == [2]

    def test_user_without_outlet_gets_empty_list(self):
        """Users without outlet should get empty allowed list"""
        user = Mock()
        user.role = UserRoleEnum.MANAGER
        user.outlet_id = None

        allowed_outlets = OutletDataAccess.get_allowed_outlet_ids(user)
        assert allowed_outlets == []