"""
backend/app/auth/permissions.py
Role-based and permission-based access control decorators and utilities.

Usage:
    from app.auth.permissions import require_role, require_permission, check_outlet_access

    @router.get("/protected")
    @require_role("admin")
    async def admin_only(current_user = Depends(get_current_user)):
        ...

    @router.get("/inventory")
    @require_permission("inventory:read")
    async def read_inventory(current_user = Depends(get_current_user)):
        ...
"""

from typing import Callable, List, Optional
from functools import wraps
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.auth import get_current_user
from app.database import get_db
from app.models.users import User


# ── Role-based decorators ──────────────────────────────────────────────────────

def require_role(*required_roles: str) -> Callable:
    """
    Decorator factory that restricts an endpoint to specific roles.
    
    Args:
        *required_roles: Role names (e.g., "admin", "manager", "staff")
        
    Returns:
        Async dependency function that checks user role
        
    Usage:
        @router.delete("/users/{id}", dependencies=[Depends(require_role("admin"))])
        async def delete_user(...): ...
        
        @router.get("/reports", dependencies=[Depends(require_role("admin", "manager"))])
        async def view_reports(...): ...
    """
    async def _check(current_user: User = Depends(get_current_user)):
        # Get role name from the Role object
        user_role = current_user.role.name if hasattr(current_user.role, 'name') else str(current_user.role)
        
        if user_role.lower() not in [r.lower() for r in required_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(required_roles)}. You have: {user_role}",
            )
        return current_user
    
    return _check


def require_roles(required_roles: List[str]) -> Callable:
    """
    Decorator that restricts an endpoint to specific roles (list variant).
    
    Args:
        required_roles: List of role names
        
    Returns:
        Async dependency function that checks user role
    """
    return require_role(*required_roles)


# ── Permission-based decorators ────────────────────────────────────────────────

def require_permission(required_permission: str) -> Callable:
    """
    Decorator factory that restricts an endpoint based on granular permissions.
    Permissions are formatted as "resource:action" (e.g., "inventory:read", "sales:create")
    
    Args:
        required_permission: Permission string in format "resource:action"
        
    Returns:
        Async dependency function that checks user permissions
        
    Usage:
        @router.get("/inventory", dependencies=[Depends(require_permission("inventory:read"))])
        async def get_inventory(...): ...
        
        @router.post("/sales", dependencies=[Depends(require_permission("sales:create"))])
        async def create_sale(...): ...
    """
    async def _check(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # Get user's role and its permissions
        role = current_user.role
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no role assigned",
            )
        
        # Check if the required permission is in the user's role permissions
        user_permissions = {perm.name for perm in role.permissions}
        
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission: {required_permission}",
            )
        
        return current_user
    
    return _check


def require_permissions(required_permissions: List[str]) -> Callable:
    """
    Decorator that checks if user has ALL specified permissions.
    
    Args:
        required_permissions: List of permission strings
        
    Returns:
        Async dependency function that checks user has all permissions
    """
    async def _check(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        role = current_user.role
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no role assigned",
            )
        
        user_permissions = {perm.name for perm in role.permissions}
        missing_perms = set(required_permissions) - user_permissions
        
        if missing_perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Missing permissions: {', '.join(missing_perms)}",
            )
        
        return current_user
    
    return _check


# ── Outlet-level access control ────────────────────────────────────────────────

def check_outlet_access(user: User, outlet_id: int) -> bool:
    """
    Verify that a user has access to a specific outlet.
    
    - Admins have access to all outlets
    - Managers and staff can only access outlets they're assigned to
    
    Args:
        user: The User object
        outlet_id: The outlet/store ID to check access for
        
    Returns:
        True if user can access the outlet, False otherwise
        
    Usage:
        async def get_outlet_data(outlet_id: int, current_user = Depends(get_current_user)):
            if not check_outlet_access(current_user, outlet_id):
                raise HTTPException(status_code=403, detail="Access denied to this outlet")
            ...
    """
    # Superadmins and admins have access to all outlets
    if current_user.is_superadmin:
        return True
    
    role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
    if role_name.lower() == "admin":
        return True
    
    # Other roles: check outlet assignments
    assigned_outlets = {outlet.store_id for outlet in user.outlets}
    return outlet_id in assigned_outlets


def check_organization_access(user: User, organization_id: str) -> bool:
    """
    Verify that a user belongs to a specific organization.
    Users can only access their own organization's data.
    
    Args:
        user: The User object
        organization_id: The organization ID to check
        
    Returns:
        True if user can access the organization, False otherwise
    """
    return str(user.organization_id) == str(organization_id)


# ── Convenience decorators for common roles ────────────────────────────────────

# FastAPI expects dependency callables (functions) directly.
# `require_role()` returns a dependency callable; expose these as variables.
require_admin = require_role("admin")
require_manager = require_role("admin", "manager")
require_staff = require_role("admin", "manager", "staff")

# Backwards compatibility helpers (if explicitly called):
# Keep them as callables for old code paths.
def require_admin_factory() -> Callable:
    """Restrict to admin users only."""
    return require_role("admin")


def require_manager_factory() -> Callable:
    """Restrict to managers and admins."""
    return require_role("admin", "manager")


def require_staff_factory() -> Callable:
    """Restrict to staff, managers, and admins (all non-guest users)."""
    return require_role("admin", "manager", "staff")


__all__ = [
    # Role-based access
    "require_role",
    "require_roles",
    "require_admin",
    "require_manager",
    "require_staff",
    # Permission-based access
    "require_permission",
    "require_permissions",
    # Outlet/org access checks
    "check_outlet_access",
    "check_organization_access",
]
