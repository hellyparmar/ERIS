"""
Base Service Class with Outlet Data Isolation

This module provides a base service class that enforces outlet-based data isolation
for all database operations. Services inheriting from this class will automatically
apply outlet filtering based on the authenticated user's role.
"""

from typing import TypeVar, Generic, Optional, List, Any
from sqlalchemy.orm import Session, Query
from sqlalchemy import select

from app.core.data_isolation import OutletDataAccess
from app.models.users import User

T = TypeVar('T')

class OutletIsolatedService(Generic[T]):
    """
    Base service class that enforces outlet-based data isolation.

    All database queries in services inheriting from this class will be
    automatically filtered based on the authenticated user's role and outlet access.
    """

    def __init__(self, db: Session, current_user: Optional[User] = None):
        self.db = db
        self.current_user = current_user
        if current_user:
            self.allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(current_user)
        else:
            self.allowed_outlet_ids = None

    def apply_outlet_filter(self, query: Query[T], outlet_column: str = 'outlet_id') -> Query[T]:
        """
        Apply outlet filtering to a query based on current user's permissions.

        Args:
            query: The query to filter
            outlet_column: Name of the outlet_id column

        Returns:
            Filtered query
        """
        if not self.current_user:
            return query
        return OutletDataAccess.apply_outlet_filter(query, self.current_user, outlet_column)

    def apply_outlet_filter_select(self, stmt: select, outlet_column: str = 'outlet_id'):
        """
        Apply outlet filtering to a select statement.

        Args:
            stmt: The select statement to filter
            outlet_column: Name of the outlet_id column

        Returns:
            Filtered select statement
        """
        if not self.current_user:
            return stmt
        return OutletDataAccess.apply_outlet_filter_select(stmt, self.current_user, outlet_column)

    def can_access_outlet(self, outlet_id: Optional[int] = None) -> bool:
        """
        Check if current user can access a specific outlet.

        Args:
            outlet_id: Outlet ID to check (None for any outlet)

        Returns:
            True if user has access
        """
        if self.allowed_outlet_ids is None:
            return True  # Admin can access all outlets

        if outlet_id is None:
            return len(self.allowed_outlet_ids) > 0

        return outlet_id in self.allowed_outlet_ids

    def get_allowed_outlets(self) -> Optional[List[int]]:
        """
        Get list of outlet IDs the current user can access.

        Returns:
            List of outlet IDs or None for admin access
        """
        return self.allowed_outlet_ids

    def validate_outlet_access(self, outlet_id: int) -> None:
        """
        Validate that current user can access the specified outlet.
        Raises HTTPException if access is denied.

        Args:
            outlet_id: Outlet ID to validate access for
        """
        from fastapi import HTTPException, status

        if not self.can_access_outlet(outlet_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: You do not have permission to access outlet {outlet_id}"
            )