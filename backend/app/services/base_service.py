"""
Base Service Class with Outlet Data Isolation

This module provides a base service class that enforces outlet-based data isolation
for all database operations. Services inheriting from this class will automatically
apply outlet filtering based on the authenticated user's role.
"""

from typing import TypeVar, Generic, Optional, List
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
            from app.api.deps import get_outlet_scope
            self.allowed_outlet_ids = get_outlet_scope(current_user, db)
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
        if self.allowed_outlet_ids is None:
            return query # super_admin
        model_class = query.column_descriptions[0]['type']
        column = getattr(model_class, outlet_column)
        return query.filter(column.in_(self.allowed_outlet_ids))

    def apply_outlet_filter_select(self, stmt: select, outlet_column: str = 'outlet_id'):
        """
        Apply outlet filtering to a SQLAlchemy 2.0 select statement.
        """
        if not self.current_user:
            return stmt
        if self.allowed_outlet_ids is None:
            return stmt
        
        model_class = stmt.column_descriptions[0]['type']
        column = getattr(model_class, outlet_column)
        return stmt.where(column.in_(self.allowed_outlet_ids))

    def can_access_outlet(self, outlet_id: Optional[int] = None) -> bool:
        """
        Check if the current user can access a specific outlet.
        If no outlet_id is provided, returns False (must specify what to check against).
        """
        if not self.current_user:
            return False
            
        if not outlet_id:
            return False
            
        if self.allowed_outlet_ids is None:
            return True # Super admin has access to everything
            
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