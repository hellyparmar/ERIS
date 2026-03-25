"""
Phase 7.1: Data Fortress - RLS Context Management
Enhanced Row-Level Security implementation with Python middleware

Handles:
- Setting PostgreSQL session variables for RLS
- User role and store assignment management
- RLS exception handling for corporate operations
- Audit logging for RLS policy evaluation
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_

logger = logging.getLogger(__name__)


class RLSContextManager:
    """
    Manages PostgreSQL RLS context and session variables
    Ensures proper tenant and role isolation
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def set_rls_context(
        self,
        user_id: UUID,
        org_id: UUID,
        user_role: str,
        assigned_stores: List[UUID],
        user_agent: Optional[str] = None
    ) -> None:
        """
        Set PostgreSQL session variables for RLS
        Must be called at the start of each request
        
        Args:
            user_id: Current user's UUID
            org_id: Current organization's UUID
            user_role: User's role (admin, owner, manager, cashier, etc.)
            assigned_stores: List of store UUIDs user has access to
            user_agent: Optional user agent string for audit
        """
        try:
            # Build comma-separated list of store IDs
            stores_string = ','.join(str(s) for s in assigned_stores) if assigned_stores else ''
            
            # Set all session variables
            self.db.execute(text("""
                SELECT set_config('app.current_user_id', :user_id, false),
                       set_config('app.current_org_id', :org_id, false),
                       set_config('app.current_user_role', :user_role, false),
                       set_config('app.current_user_stores', :stores, false),
                       set_config('app.user_agent', :user_agent, false),
                       set_config('app.request_timestamp', :timestamp, false)
            """), {
                'user_id': str(user_id),
                'org_id': str(org_id),
                'user_role': user_role,
                'stores': stores_string,
                'user_agent': user_agent or 'unknown',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(
                f"RLS context set for user {user_id} in org {org_id} "
                f"with role {user_role} and {len(assigned_stores)} stores"
            )
        except Exception as e:
            logger.error(f"Failed to set RLS context: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to establish secure session context"
            )
    
    def clear_rls_context(self) -> None:
        """
        Clear all RLS session variables
        Called at end of request for security
        """
        try:
            self.db.execute(text("""
                SELECT reset_config('app.current_user_id'),
                       reset_config('app.current_org_id'),
                       reset_config('app.current_user_role'),
                       reset_config('app.current_user_stores'),
                       reset_config('app.user_agent'),
                       reset_config('app.request_timestamp')
            """))
            logger.debug("RLS context cleared")
        except Exception as e:
            logger.warning(f"Failed to clear RLS context: {str(e)}")
    
    def verify_rls_enabled(self) -> Dict[str, Any]:
        """
        Verify that RLS is properly enabled on all critical tables
        Returns detailed status report
        """
        result = self.db.execute(text("""
            SELECT table_name, rls_enabled, policy_count FROM verify_rls_enabled()
        """)).fetchall()
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'tables': [],
            'all_protected': True,
            'total_tables': len(result),
            'protected_count': 0
        }
        
        for row in result:
            table_info = {
                'table': row[0],
                'rls_enabled': row[1],
                'policy_count': row[2]
            }
            report['tables'].append(table_info)
            
            if row[1]:
                report['protected_count'] += 1
            else:
                report['all_protected'] = False
                logger.warning(f"RLS not enabled on table: {row[0]}")
        
        return report
    
    def grant_rls_exception(
        self,
        granted_to_user_id: UUID,
        target_org_id: UUID,
        table_name: str,
        access_type: str,
        expires_hours: int,
        reason: str,
        current_user_id: UUID
    ) -> Dict[str, Any]:
        """
        Grant temporary cross-organization access exception
        Only callable by organization admins
        
        Args:
            granted_to_user_id: User receiving the exception
            target_org_id: Organization they can access
            table_name: Which table(s) they can access
            access_type: SELECT, INSERT, UPDATE, DELETE, or ALL
            expires_hours: Hours until exception expires
            reason: Audit trail reason
            current_user_id: User granting the exception
            
        Returns:
            Exception ID and details
        """
        try:
            # Verify grantor is admin (this check happens in DB too)
            result = self.db.execute(text("""
                SELECT grant_rls_exception(
                    :granted_to,
                    :target_org,
                    :table_name,
                    :access_type,
                    :expires_hours,
                    :reason
                )
            """), {
                'granted_to': str(granted_to_user_id),
                'target_org': str(target_org_id),
                'table_name': table_name,
                'access_type': access_type,
                'expires_hours': expires_hours,
                'reason': reason
            }).scalar()
            
            logger.info(
                f"RLS exception {result} granted to {granted_to_user_id} "
                f"for {table_name} in org {target_org_id}"
            )
            
            return {
                'exception_id': result,
                'granted_to': str(granted_to_user_id),
                'target_org': str(target_org_id),
                'table': table_name,
                'access_type': access_type,
                'expires_in_hours': expires_hours,
                'reason': reason,
                'created_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to grant RLS exception: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot grant RLS exception: {str(e)}"
            )
    
    def revoke_rls_exception(self, exception_id: int) -> bool:
        """
        Revoke an RLS exception
        Only callable by organization admins
        """
        try:
            self.db.execute(text("""
                SELECT revoke_rls_exception(:exception_id)
            """), {'exception_id': exception_id})
            
            logger.info(f"RLS exception {exception_id} revoked")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke RLS exception {exception_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot revoke RLS exception"
            )
    
    def list_active_exceptions(self) -> List[Dict[str, Any]]:
        """
        List all active RLS exceptions for current organization
        Only callable by organization admins
        """
        try:
            result = self.db.execute(text("""
                SELECT * FROM list_rls_exceptions()
            """)).fetchall()
            
            exceptions = []
            for row in result:
                exceptions.append({
                    'exception_id': row[0],
                    'granted_to': row[1],
                    'target_org_id': str(row[2]),
                    'table': row[3],
                    'access_type': row[4],
                    'expires_at': row[5].isoformat() if row[5] else None,
                    'reason': row[6]
                })
            
            return exceptions
        except Exception as e:
            logger.error(f"Failed to list RLS exceptions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot list RLS exceptions"
            )
    
    def get_violation_report(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get RLS violation statistics for monitoring
        Shows attempts to access data outside user's scope
        """
        try:
            result = self.db.execute(text("""
                SELECT * FROM rls_violation_report
            """)).fetchall()
            
            violations = {
                'timestamp': datetime.utcnow().isoformat(),
                'report_hours': hours,
                'total_violations': 0,
                'by_table': {},
                'by_type': {}
            }
            
            for row in result:
                # row: hour, table_name, violation_type, violation_count, unique_users, unique_orgs
                hour = row[0]
                table = row[1]
                violation_type = row[2]
                count = row[3]
                
                violations['total_violations'] += count
                
                if table not in violations['by_table']:
                    violations['by_table'][table] = 0
                violations['by_table'][table] += count
                
                if violation_type not in violations['by_type']:
                    violations['by_type'][violation_type] = 0
                violations['by_type'][violation_type] += count
            
            return violations
        except Exception as e:
            logger.warning(f"Failed to get violation report: {str(e)}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def cleanup_expired_resources(self) -> Dict[str, int]:
        """
        Clean up expired RLS exceptions and old violations
        Should be called daily
        """
        cleanup_stats = {}
        
        try:
            # Clean expired exceptions
            result = self.db.execute(text("""
                SELECT cleanup_expired_rls_exceptions()
            """)).scalar()
            cleanup_stats['expired_exceptions_deleted'] = result or 0
            
            # Clean old violations
            result = self.db.execute(text("""
                SELECT cleanup_old_rls_violations()
            """)).scalar()
            cleanup_stats['old_violations_deleted'] = result or 0
            
            logger.info(f"RLS cleanup completed: {cleanup_stats}")
            return cleanup_stats
        except Exception as e:
            logger.error(f"Failed to cleanup RLS resources: {str(e)}")
            return {'error': str(e)}


class RLSMiddleware:
    """
    FastAPI middleware that automatically sets RLS context for each request
    Integrates with JWT token and user database
    """
    
    def __init__(self, db_factory):
        self.db_factory = db_factory
    
    async def __call__(self, request: Request, call_next):
        """
        Process request and set RLS context
        """
        # Extract user info from request (from JWT middleware)
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else None
        org_id = request.state.org_id if hasattr(request.state, 'org_id') else None
        user_role = request.state.user_role if hasattr(request.state, 'user_role') else None
        assigned_stores = request.state.assigned_stores if hasattr(request.state, 'assigned_stores') else []
        
        db = self.db_factory()
        
        try:
            if user_id and org_id:
                # Set RLS context for this request
                rls_mgr = RLSContextManager(db)
                rls_mgr.set_rls_context(
                    user_id=user_id,
                    org_id=org_id,
                    user_role=user_role or 'user',
                    assigned_stores=assigned_stores or [],
                    user_agent=request.headers.get('user-agent')
                )
            
            # Process request
            response = await call_next(request)
            
            return response
        finally:
            # Always clear context after request
            if user_id and org_id:
                rls_mgr = RLSContextManager(db)
                rls_mgr.clear_rls_context()
            db.close()


class RLSValidator:
    """
    Validates that user can access requested resource
    Works alongside PostgreSQL RLS for defense-in-depth
    """
    
    @staticmethod
    def user_can_access_org(user_org_id: UUID, requested_org_id: UUID) -> bool:
        """Check if user can access organization"""
        return user_org_id == requested_org_id
    
    @staticmethod
    def user_can_access_store(
        user_stores: List[UUID],
        requested_store_id: UUID,
        user_role: str
    ) -> bool:
        """Check if user can access store"""
        # Managers can access all stores in their org
        if user_role in ['admin', 'owner', 'manager']:
            return True
        # Others only their assigned stores
        return requested_store_id in user_stores
    
    @staticmethod
    def user_can_modify_invoice(
        user_org_id: UUID,
        invoice_org_id: UUID,
        user_role: str,
        invoice_created_at: datetime
    ) -> bool:
        """
        Check if user can modify invoice
        Managers can only modify recent invoices (configurable)
        """
        if user_org_id != invoice_org_id:
            return False
        
        # Owners/Admins can modify any
        if user_role in ['admin', 'owner']:
            return True
        
        # Managers only recent invoices (30 days)
        if user_role == 'manager':
            days_old = (datetime.utcnow() - invoice_created_at).days
            return days_old <= 30
        
        # Others cannot modify
        return False


# Configuration constants
RLS_CONFIG = {
    'SESSION_TIMEOUT_MINUTES': 30,
    'VIOLATION_LOG_RETENTION_DAYS': 90,
    'EXCEPTION_DEFAULT_EXPIRY_HOURS': 24,
    'EXCEPTION_MAX_EXPIRY_HOURS': 168,  # 1 week
    'CLEANUP_SCHEDULE': '0 2 * * *',  # 2 AM daily
}
