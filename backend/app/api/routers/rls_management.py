"""
Phase 7.1: RLS Management API Routes
Admin endpoints for managing Row-Level Security policies and exceptions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime

from app.api.db import get_db
from app.api.auth.dependencies import get_current_user
from app.api.security.rls_context import RLSContextManager, RLSValidator
from app.api.schemas.rls import (
    RLSExceptionCreate,
    RLSExceptionResponse,
    RLSViolationReport,
    RLSStatusReport,
    RLSContextInfo
)

router = APIRouter(prefix="/api/v1/admin/rls", tags=["RLS Management"])


# ============================================================
# RLS STATUS & MONITORING
# ============================================================

@router.get("/status", response_model=RLSStatusReport)
async def get_rls_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> RLSStatusReport:
    """
    Get current RLS status and protection coverage
    
    Checks:
    - RLS enabled on all critical tables
    - Number of policies per table
    - Recent violations
    - Active exceptions
    
    **Requires:** Admin role
    """
    if current_user['role'] not in ['admin', 'owner']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view RLS status"
        )
    
    rls_mgr = RLSContextManager(db)
    verification = rls_mgr.verify_rls_enabled()
    violations = rls_mgr.get_violation_report(hours=24)
    
    return RLSStatusReport(
        timestamp=datetime.utcnow(),
        verification=verification,
        violations_24h=violations.get('total_violations', 0),
        status="protected" if verification['all_protected'] else "warning"
    )


@router.get("/violations", response_model=RLSViolationReport)
async def get_violation_report(
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> RLSViolationReport:
    """
    Get detailed RLS violation report
    
    Shows attempts to access data outside user's authorized scope
    Useful for security monitoring and debugging
    
    **Requires:** Admin role
    """
    if current_user['role'] not in ['admin', 'owner']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view violation reports"
        )
    
    rls_mgr = RLSContextManager(db)
    return rls_mgr.get_violation_report(hours=hours)


@router.get("/context", response_model=RLSContextInfo)
async def get_current_context(
    current_user: dict = Depends(get_current_user)
) -> RLSContextInfo:
    """
    Get current request's RLS context
    
    Returns:
    - Current user ID and organization
    - User role
    - Assigned stores
    - Effective permissions
    
    Useful for debugging access issues
    """
    return RLSContextInfo(
        user_id=current_user['id'],
        org_id=current_user['org_id'],
        user_role=current_user['role'],
        assigned_stores=current_user.get('assigned_stores', []),
        timestamp=datetime.utcnow()
    )


# ============================================================
# RLS EXCEPTION MANAGEMENT
# ============================================================

@router.post("/exceptions", response_model=RLSExceptionResponse, status_code=status.HTTP_201_CREATED)
async def create_rls_exception(
    exception_data: RLSExceptionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> RLSExceptionResponse:
    """
    Grant temporary RLS exception (cross-organization access)
    
    Used for:
    - Audit operations by corporate team
    - Data consolidation/migration
    - Executive reporting
    - Support/troubleshooting
    
    Exceptions are:
    - Time-limited (configurable expiry)
    - Audit-logged (who granted, to whom, when)
    - Role-restricted (only admins)
    - Table-specific (not blanket access)
    
    **Requires:** Admin role
    
    Example:
    ```json
    {
        "granted_to_user_id": "user-uuid",
        "target_org_id": "org-uuid",
        "table_name": "invoices",
        "access_type": "SELECT",
        "expires_hours": 24,
        "reason": "Executive audit of Q4 sales"
    }
    ```
    """
    if current_user['role'] not in ['admin', 'owner']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can grant RLS exceptions"
        )
    
    # Validate data
    if exception_data.expires_hours > 168:  # 1 week max
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exception expiry cannot exceed 168 hours (7 days)"
        )
    
    rls_mgr = RLSContextManager(db)
    
    result = rls_mgr.grant_rls_exception(
        granted_to_user_id=exception_data.granted_to_user_id,
        target_org_id=exception_data.target_org_id,
        table_name=exception_data.table_name,
        access_type=exception_data.access_type,
        expires_hours=exception_data.expires_hours,
        reason=exception_data.reason,
        current_user_id=current_user['id']
    )
    
    return RLSExceptionResponse(**result)


@router.get("/exceptions", response_model=List[RLSExceptionResponse])
async def list_rls_exceptions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> List[RLSExceptionResponse]:
    """
    List all active RLS exceptions for current organization
    
    Shows:
    - Who was granted access
    - What data they can access
    - When the exception expires
    - The reason for the grant
    
    **Requires:** Admin role
    """
    if current_user['role'] not in ['admin', 'owner']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view RLS exceptions"
        )
    
    rls_mgr = RLSContextManager(db)
    exceptions = rls_mgr.list_active_exceptions()
    
    return [RLSExceptionResponse(**exc) for exc in exceptions]


@router.delete("/exceptions/{exception_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_rls_exception(
    exception_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> None:
    """
    Revoke an RLS exception immediately
    
    The user loses cross-organization access immediately
    Event is logged for audit trail
    
    **Requires:** Admin role
    """
    if current_user['role'] not in ['admin', 'owner']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can revoke RLS exceptions"
        )
    
    rls_mgr = RLSContextManager(db)
    rls_mgr.revoke_rls_exception(exception_id)


# ============================================================
# RLS VALIDATION & TESTING
# ============================================================

@router.post("/validate/org")
async def validate_org_access(
    org_id: UUID,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Test if current user can access specified organization
    
    Returns:
    - Whether access is allowed
    - Reason if denied
    - Active exceptions if applicable
    
    Useful for debugging access issues
    """
    can_access = RLSValidator.user_can_access_org(
        user_org_id=UUID(current_user['org_id']),
        requested_org_id=org_id
    )
    
    return {
        'can_access': can_access,
        'user_org': current_user['org_id'],
        'requested_org': str(org_id),
        'reason': 'User is in requested organization' if can_access else 'User is in different organization'
    }


@router.post("/validate/store")
async def validate_store_access(
    store_id: UUID,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Test if current user can access specified store
    
    Considers:
    - User role (managers can access all stores)
    - Assigned stores (cashiers limited to assigned)
    """
    can_access = RLSValidator.user_can_access_store(
        user_stores=current_user.get('assigned_stores', []),
        requested_store_id=store_id,
        user_role=current_user['role']
    )
    
    return {
        'can_access': can_access,
        'user_role': current_user['role'],
        'assigned_stores': current_user.get('assigned_stores', []),
        'requested_store': str(store_id),
        'reason': (
            'User has manager role or higher' if current_user['role'] in ['admin', 'owner', 'manager']
            else 'Store is assigned to user' if can_access
            else 'User not assigned to this store'
        )
    }


# ============================================================
# RLS CLEANUP & MAINTENANCE
# ============================================================

@router.post("/cleanup", status_code=status.HTTP_202_ACCEPTED)
async def trigger_rls_cleanup(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Manually trigger RLS cleanup jobs
    
    Cleans up:
    - Expired RLS exceptions
    - Old violation records (>90 days)
    
    Normally runs automatically via scheduled job (2 AM daily)
    
    **Requires:** Admin role
    """
    if current_user['role'] not in ['admin', 'owner']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can trigger cleanup"
        )
    
    rls_mgr = RLSContextManager(db)
    stats = rls_mgr.cleanup_expired_resources()
    
    return {
        'status': 'cleanup_completed',
        'timestamp': datetime.utcnow().isoformat(),
        **stats
    }


# ============================================================
# RLS DOCUMENTATION & HELP
# ============================================================

@router.get("/documentation")
async def get_rls_documentation() -> Dict[str, Any]:
    """
    Get RLS system documentation
    
    Includes:
    - How RLS works
    - Access control rules
    - Common scenarios
    - Troubleshooting
    """
    return {
        'title': 'Row-Level Security (RLS) Documentation',
        'version': '7.1',
        'description': 'Multi-tenant data isolation and role-based access control',
        'features': [
            'Organization-level isolation (complete data separation)',
            'Store-level filtering (users see only assigned stores)',
            'Role-based permissions (admin/manager/cashier)',
            'Time-based controls (business hours restrictions)',
            'Temporary exceptions (audits, corporate operations)',
            'Violation monitoring (security awareness)',
            'Audit trail (compliance tracking)'
        ],
        'roles_and_access': {
            'admin': {
                'description': 'Full access across all organizations',
                'can_view': 'All data',
                'can_modify': 'All data',
                'can_grant_exceptions': True,
                'can_manage_rls': True
            },
            'owner': {
                'description': 'Full access to organization data',
                'can_view': 'Organization data only',
                'can_modify': 'Organization data only',
                'can_grant_exceptions': True,
                'can_manage_rls': True
            },
            'manager': {
                'description': 'Management access to stores',
                'can_view': 'All stores in organization',
                'can_modify': 'Recent data only (30 days)',
                'can_grant_exceptions': False,
                'can_manage_rls': False
            },
            'cashier': {
                'description': 'Point of sale access',
                'can_view': 'Assigned stores only',
                'can_modify': 'Current transactions only',
                'can_grant_exceptions': False,
                'can_manage_rls': False
            },
            'analyst': {
                'description': 'Read-only analytics access',
                'can_view': 'Organization reports',
                'can_modify': 'None',
                'can_grant_exceptions': False,
                'can_manage_rls': False
            }
        },
        'api_endpoints': {
            'status': 'GET /api/v1/admin/rls/status',
            'violations': 'GET /api/v1/admin/rls/violations',
            'context': 'GET /api/v1/admin/rls/context',
            'create_exception': 'POST /api/v1/admin/rls/exceptions',
            'list_exceptions': 'GET /api/v1/admin/rls/exceptions',
            'revoke_exception': 'DELETE /api/v1/admin/rls/exceptions/{id}',
            'validate_org': 'POST /api/v1/admin/rls/validate/org',
            'validate_store': 'POST /api/v1/admin/rls/validate/store',
            'cleanup': 'POST /api/v1/admin/rls/cleanup'
        },
        'database_functions': [
            'current_user_id() - Get session user',
            'current_org_id() - Get session organization',
            'current_user_role() - Get session role',
            'current_user_stores() - Get assigned stores',
            'is_admin() - Check admin privileges',
            'has_rls_exception() - Check if exception exists',
            'grant_rls_exception() - Grant temporary access',
            'revoke_rls_exception() - Revoke access',
            'list_rls_exceptions() - List active exceptions',
            'cleanup_expired_rls_exceptions() - Clean up expired',
            'cleanup_old_rls_violations() - Archive violations'
        ],
        'monitoring': {
            'violation_tracking': 'All access attempts logged',
            'audit_trail': '90-day retention',
            'exception_tracking': 'Full audit of grants/revokes',
            'performance': 'RLS indexes optimized for fast evaluation'
        }
    }
