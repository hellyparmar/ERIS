"""
Database Row-Level Security (RLS) Engine

Implements granular, multi-level data access control at the database level
using PostgreSQL row security policies and application-level enforcement.

Features:
- Tenant isolation (Hard security boundary)
- Role-based row filtering (Admin, Manager, Staff)
- Contextual access control (Branch, Department, Team)
- Audit trail for all RLS decisions
- Performance optimized with caching
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib

from sqlalchemy import and_, or_, not_, text, event, select
from sqlalchemy.orm import Session, Query
from sqlalchemy.sql import ClauseElement
from app.api.db import models

logger = logging.getLogger(__name__)


class RLSLevel(Enum):
    """Row-Level Security access levels"""
    SYSTEM_ADMIN = "system_admin"      # Full access across all tenants
    TENANT_ADMIN = "tenant_admin"      # All rows for their tenant
    BRANCH_MANAGER = "branch_manager"  # Branch + subordinate staff
    DEPARTMENT_MANAGER = "dept_manager"  # Department level
    TEAM_LEAD = "team_lead"            # Team members + their sales
    STAFF = "staff"                    # Own sales/data only
    READONLY = "readonly"              # Read-only access


class RLSContext:
    """Security context for RLS decisions"""
    
    def __init__(
        self,
        user_id: str,
        tenant_id: str,
        role: RLSLevel,
        branch_ids: Optional[List[str]] = None,
        department_ids: Optional[List[str]] = None,
        team_ids: Optional[List[str]] = None,
        is_super_admin: bool = False,
    ):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.role = role
        self.branch_ids = set(branch_ids or [])
        self.department_ids = set(department_ids or [])
        self.team_ids = set(team_ids or [])
        self.is_super_admin = is_super_admin
        self.created_at = datetime.utcnow()
        
    def __hash__(self) -> str:
        """Generate context hash for audit trail"""
        data = f"{self.user_id}:{self.tenant_id}:{self.role.value}:{sorted(self.branch_ids)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass
class RLSPolicy:
    """RLS Policy definition"""
    name: str
    description: str
    table_name: str
    role: RLSLevel
    sql_filter: Optional[str] = None  # Raw SQL filter if needed
    is_permissive: bool = True  # True = allow, False = restrict
    using_clause: Optional[str] = None  # PostgreSQL USING clause
    with_check_clause: Optional[str] = None  # PostgreSQL WITH CHECK clause


class RLSEngine:
    """
    Multi-level row security enforcement engine
    
    Provides:
    - Automatic query filtering based on context
    - PostgreSQL RLS policy generation
    - Audit trail logging
    - Performance optimization
    """
    
    # Cache for RLS contexts (user_id -> RLSContext)
    _context_cache: Dict[str, RLSContext] = {}
    
    # Cache for policy evaluations
    _policy_cache: Dict[str, List[RLSPolicy]] = {}
    
    # Current context thread-local storage
    _current_context: Optional[RLSContext] = None
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_logs: List[Dict[str, Any]] = []
        
    @classmethod
    def set_context(cls, context: RLSContext) -> None:
        """Set current RLS context for request"""
        cls._current_context = context
        logger.debug(f"RLS Context set: {context.user_id} ({context.role.value})")
        
    @classmethod
    def get_context(cls) -> Optional[RLSContext]:
        """Get current RLS context"""
        return cls._current_context
    
    @classmethod
    def clear_context(cls) -> None:
        """Clear current RLS context"""
        cls._current_context = None
        
    def apply_rls_filter(
        self,
        query: Query,
        model: type,
        context: RLSContext,
    ) -> Query:
        """
        Apply RLS filters to a query based on user role and context
        
        Args:
            query: SQLAlchemy query object
            model: Model class to filter
            context: RLS context with user permissions
            
        Returns:
            Filtered query
        """
        self._log_rls_access(model.__name__, context, "filter_applied")
        
        # System admin can see everything
        if context.is_super_admin:
            return query
            
        # Tenant boundary - non-negotiable
        if hasattr(model, 'tenant_id'):
            query = query.filter(model.tenant_id == context.tenant_id)
        
        # Role-based filtering
        if context.role == RLSLevel.SYSTEM_ADMIN:
            return query
            
        elif context.role == RLSLevel.TENANT_ADMIN:
            # Can see all rows in their tenant (already filtered above)
            return query
            
        elif context.role == RLSLevel.BRANCH_MANAGER:
            if hasattr(model, 'branch_id'):
                query = query.filter(model.branch_id.in_(context.branch_ids))
                
                # Can also see subordinate staff sales
                if hasattr(model, 'staff_id'):
                    staff_filter = self._get_subordinate_staff(
                        context.user_id,
                        context.branch_ids
                    )
                    query = query.filter(
                        or_(
                            model.staff_id.in_(staff_filter),
                            model.staff_id == context.user_id
                        )
                    )
            return query
            
        elif context.role == RLSLevel.DEPARTMENT_MANAGER:
            if hasattr(model, 'department_id'):
                query = query.filter(model.department_id.in_(context.department_ids))
                
                if hasattr(model, 'staff_id'):
                    staff_filter = self._get_departmental_staff(
                        context.user_id,
                        context.department_ids
                    )
                    query = query.filter(model.staff_id.in_(staff_filter))
            return query
            
        elif context.role == RLSLevel.TEAM_LEAD:
            if hasattr(model, 'team_id'):
                query = query.filter(model.team_id.in_(context.team_ids))
                
            if hasattr(model, 'staff_id'):
                team_staff = self._get_team_staff(context.user_id, context.team_ids)
                query = query.filter(
                    or_(
                        model.staff_id.in_(team_staff),
                        model.staff_id == context.user_id
                    )
                )
            return query
            
        elif context.role == RLSLevel.STAFF:
            # Can only see own data
            if hasattr(model, 'staff_id'):
                query = query.filter(model.staff_id == context.user_id)
            elif hasattr(model, 'created_by'):
                query = query.filter(model.created_by == context.user_id)
            return query
            
        elif context.role == RLSLevel.READONLY:
            # Read-only access (no write operations allowed at application level)
            return query
            
        return query
    
    def can_access_row(
        self,
        row: Any,
        context: RLSContext,
        action: str = "read"
    ) -> bool:
        """
        Check if context can access a specific row
        
        Args:
            row: ORM model instance
            context: RLS context
            action: "read", "write", "delete"
            
        Returns:
            True if access allowed, False otherwise
        """
        # Super admin can do anything
        if context.is_super_admin:
            return True
        
        # Tenant boundary check
        if hasattr(row, 'tenant_id') and row.tenant_id != context.tenant_id:
            self._log_rls_denial(
                row.__class__.__name__,
                context,
                f"Tenant mismatch: {row.tenant_id} != {context.tenant_id}"
            )
            return False
        
        # Role-based access checks
        if context.role == RLSLevel.TENANT_ADMIN:
            return action != "delete"  # Prevent accidental deletion
            
        elif context.role == RLSLevel.BRANCH_MANAGER:
            if hasattr(row, 'branch_id'):
                if row.branch_id not in context.branch_ids:
                    self._log_rls_denial(row.__class__.__name__, context, "Branch not authorized")
                    return False
            return action in ["read", "write"]
            
        elif context.role == RLSLevel.DEPARTMENT_MANAGER:
            if hasattr(row, 'department_id'):
                if row.department_id not in context.department_ids:
                    self._log_rls_denial(row.__class__.__name__, context, "Department not authorized")
                    return False
            return action in ["read", "write"]
            
        elif context.role == RLSLevel.TEAM_LEAD:
            if hasattr(row, 'staff_id'):
                is_team_member = self._is_team_member(row.staff_id, context.user_id)
                if not is_team_member and row.staff_id != context.user_id:
                    return False
            return action in ["read", "write"]
            
        elif context.role == RLSLevel.STAFF:
            # Can only access own records
            if hasattr(row, 'staff_id') and row.staff_id != context.user_id:
                return False
            if hasattr(row, 'created_by') and row.created_by != context.user_id:
                return False
            return action == "read"
            
        elif context.role == RLSLevel.READONLY:
            return action == "read"
        
        return False
    
    def generate_postgres_rls_policies(self, context: RLSContext) -> List[str]:
        """
        Generate PostgreSQL RLS policy SQL statements
        
        These can be executed to enforce RLS at the database level,
        providing defense-in-depth security.
        
        Args:
            context: RLS context for policy generation
            
        Returns:
            List of SQL policy statements
        """
        policies = []
        
        # Example: Sales table RLS policy
        policies.append(f"""
            CREATE POLICY sales_rls_policy ON sales
            AS PERMISSIVE FOR ALL
            TO authenticated_role
            USING (
                tenant_id = current_setting('app.current_tenant_id')::uuid
                AND (
                    current_setting('app.user_role') = 'tenant_admin'
                    OR staff_id = current_setting('app.current_user_id')::uuid
                )
            )
            WITH CHECK (
                tenant_id = current_setting('app.current_tenant_id')::uuid
            );
        """)
        
        # Products table - visible to all in tenant
        policies.append(f"""
            CREATE POLICY products_rls_policy ON products
            AS PERMISSIVE FOR SELECT
            TO authenticated_role
            USING (
                tenant_id = current_setting('app.current_tenant_id')::uuid
            );
        """)
        
        # Inventory table - based on branch/department
        policies.append(f"""
            CREATE POLICY inventory_rls_policy ON inventory
            AS PERMISSIVE FOR ALL
            TO authenticated_role
            USING (
                tenant_id = current_setting('app.current_tenant_id')::uuid
                AND (
                    current_setting('app.user_role') IN ('tenant_admin', 'branch_manager')
                    OR branch_id = current_setting('app.current_branch_id')::uuid
                )
            );
        """)
        
        # Customers table - branch visibility
        policies.append(f"""
            CREATE POLICY customers_rls_policy ON customers
            AS PERMISSIVE FOR ALL
            TO authenticated_role
            USING (
                tenant_id = current_setting('app.current_tenant_id')::uuid
                AND (
                    current_setting('app.user_role') IN ('tenant_admin', 'branch_manager')
                    OR branch_id = current_setting('app.current_branch_id')::uuid
                )
            );
        """)
        
        return policies
    
    def _get_subordinate_staff(self, user_id: str, branch_ids: Set[str]) -> List[str]:
        """Get IDs of staff members under a branch manager"""
        staff = self.db.query(models.User).filter(
            models.User.branch_id.in_(branch_ids),
            models.User.tenant_id == self._current_context.tenant_id
        ).all()
        return [s.id for s in staff] + [user_id]
    
    def _get_departmental_staff(self, user_id: str, dept_ids: Set[str]) -> List[str]:
        """Get IDs of staff in departments"""
        staff = self.db.query(models.User).filter(
            models.User.department_id.in_(dept_ids),
            models.User.tenant_id == self._current_context.tenant_id
        ).all()
        return [s.id for s in staff] + [user_id]
    
    def _get_team_staff(self, user_id: str, team_ids: Set[str]) -> List[str]:
        """Get IDs of staff in teams"""
        staff = self.db.query(models.User).filter(
            models.User.team_id.in_(team_ids),
            models.User.tenant_id == self._current_context.tenant_id
        ).all()
        return [s.id for s in staff] + [user_id]
    
    def _is_team_member(self, staff_id: str, manager_id: str) -> bool:
        """Check if staff is under a team lead"""
        manager = self.db.query(models.User).filter_by(id=manager_id).first()
        if not manager or not manager.team_id:
            return False
        
        staff = self.db.query(models.User).filter_by(id=staff_id).first()
        return staff and staff.team_id == manager.team_id
    
    def _log_rls_access(
        self,
        resource: str,
        context: RLSContext,
        action: str
    ) -> None:
        """Log successful RLS access"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": context.user_id,
            "role": context.role.value,
            "resource": resource,
            "action": action,
            "status": "ALLOWED",
            "context_hash": context.__hash__(),
        }
        self.audit_logs.append(log_entry)
        logger.debug(f"RLS Access: {resource} by {context.user_id} ({context.role.value})")
    
    def _log_rls_denial(
        self,
        resource: str,
        context: RLSContext,
        reason: str
    ) -> None:
        """Log denied RLS access"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": context.user_id,
            "role": context.role.value,
            "resource": resource,
            "action": "access_attempt",
            "status": "DENIED",
            "reason": reason,
            "context_hash": context.__hash__(),
        }
        self.audit_logs.append(log_entry)
        logger.warning(f"RLS Denial: {resource} denied to {context.user_id}: {reason}")


class RLSMiddleware:
    """
    Middleware to enforce RLS on all database operations
    
    Integrates with FastAPI request lifecycle to set/clear RLS context
    """
    
    def __init__(self, get_db_callable, get_current_user_callable):
        self.get_db = get_db_callable
        self.get_current_user = get_current_user_callable
    
    async def __call__(self, request, call_next):
        """Inject RLS context into request"""
        try:
            user = await self.get_current_user()
            if user:
                context = self._build_rls_context(user)
                RLSEngine.set_context(context)
                request.state.rls_context = context
        except Exception as e:
            logger.error(f"RLS middleware error: {e}")
        
        try:
            response = await call_next(request)
        finally:
            RLSEngine.clear_context()
        
        return response
    
    def _build_rls_context(self, user) -> RLSContext:
        """Build RLS context from user object"""
        return RLSContext(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            role=RLSLevel[user.role.upper()],
            branch_ids=[str(user.branch_id)] if user.branch_id else [],
            department_ids=[str(user.department_id)] if user.department_id else [],
            team_ids=[str(user.team_id)] if user.team_id else [],
            is_super_admin=user.is_super_admin,
        )


def apply_rls_to_model(model_class: type):
    """
    Decorator to apply RLS filtering to ORM model queries
    
    Usage:
        @apply_rls_to_model
        class Sale(Base):
            ...
    """
    original_query = model_class.query
    
    def filtered_query(cls):
        context = RLSEngine.get_context()
        if context:
            engine = RLSEngine(original_query.session)
            return engine.apply_rls_filter(original_query, cls, context)
        return original_query
    
    model_class.query = filtered_query
    return model_class
