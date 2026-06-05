"""
Data Isolation Utilities for Role-Based Access Control

This module provides utilities for enforcing outlet-based data isolation
in the Enterprise Retail Intelligence System. It ensures that users with
Manager and Analyst roles can only access data from their assigned outlet,
while Admin users can access data across all outlets.
"""

from typing import Type, TypeVar, Optional, List, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Query
from sqlalchemy.sql import Select

from app.models.users import UserRoleEnum

T = TypeVar('T')

class OutletDataAccess:
    """
    Utility class for enforcing outlet-based data isolation.

    This class provides methods to filter database queries based on user roles:
    - Admin users: No filtering (access to all outlets)
    - Manager/Analyst users: Filtered to their assigned outlet only
    """

    @staticmethod
    def get_allowed_outlet_ids(user) -> Optional[List[int]]:
        """
        Get the list of outlet IDs the user is allowed to access.

        Args:
            user: The authenticated user

        Returns:
            List of outlet IDs, or None if user can access all outlets
        """
        if user.role == UserRoleEnum.ADMIN:
            return None  # Admin can access all outlets

        if user.role in [UserRoleEnum.MANAGER, UserRoleEnum.STAFF]:  # STAFF includes Analysts
            if user.outlet_id:
                return [user.outlet_id]
            else:
                return []  # User has no outlet assigned

        # Default: no access
        return []

    @staticmethod
    def apply_outlet_filter(query: Query[T], user, outlet_column: str = 'outlet_id') -> Query[T]:
        """
        Apply outlet-based filtering to a SQLAlchemy query.

        Args:
            query: The base query to filter
            user: The authenticated user
            outlet_column: Name of the outlet_id column (default: 'outlet_id')

        Returns:
            Filtered query
        """
        allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(user)

        if allowed_outlet_ids is None:
            # Admin user - no filtering needed
            return query

        if not allowed_outlet_ids:
            # User has no outlet access - return empty query
            return query.filter(False)

        # Get the model class from the query
        model_class = query.column_descriptions[0]['entity']

        # Filter to allowed outlets
        outlet_filter = getattr(model_class, outlet_column).in_(allowed_outlet_ids)
        return query.filter(outlet_filter)

    @staticmethod
    def apply_outlet_filter_select(stmt: Select, user, outlet_column: str = 'outlet_id') -> Select:
        """
        Apply outlet-based filtering to a SQLAlchemy select statement.

        Args:
            stmt: The select statement to filter
            user: The authenticated user
            outlet_column: Name of the outlet_id column (default: 'outlet_id')

        Returns:
            Filtered select statement
        """
        allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(user)

        if allowed_outlet_ids is None:
            # Admin user - no filtering needed
            return stmt

        if not allowed_outlet_ids:
            # User has no outlet access - return empty result
            return stmt.where(False)

        # Get the table/entity from the select statement
        # This is a simplified approach - in practice you might need to be more specific
        from sqlalchemy import inspect
        entity = None
        for column in stmt.columns:
            if hasattr(column, 'table'):
                entity = column.table
                break

        if entity and hasattr(entity.c, outlet_column):
            outlet_filter = entity.c[outlet_column].in_(allowed_outlet_ids)
            return stmt.where(outlet_filter)

        return stmt

def require_outlet_access(user, requested_outlet_id: Optional[int] = None) -> bool:
    """
    Check if a user has access to a specific outlet or any outlet.

    Args:
        user: The authenticated user
        requested_outlet_id: Specific outlet ID to check (None for any outlet)

    Returns:
        True if user has access, False otherwise
    """
    allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(user)

    if allowed_outlet_ids is None:
        # Admin can access any outlet
        return True

    if requested_outlet_id is None:
        # Check if user can access any outlet
        return len(allowed_outlet_ids) > 0

    # Check if user can access the specific outlet
    return requested_outlet_id in allowed_outlet_ids