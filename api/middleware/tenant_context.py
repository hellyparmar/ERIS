"""
Tenant Context Middleware
Sets organization context for Row-Level Security (RLS)
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to set tenant (organization) context for each request
    
    Sets PostgreSQL session variable 'app.current_org_id' used by RLS policies
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            # Get user from request (set by authentication middleware)
            user = getattr(request.state, 'user', None)
            
            if user:
                organization_id = user.get('organization_id')
                
                if organization_id:
                    # Set PostgreSQL session variable for RLS
                    await self._set_org_context(request, str(organization_id))
                    
                    # Store in request state for easy access
                    request.state.organization_id = organization_id
                    request.state.tenant_id = organization_id  # Alias
                    
                    logger.debug(f"Tenant context set: org={organization_id}")
                else:
                    logger.warning(f"User {user.get('id')} has no organization_id")
            
            # Process request
            response = await call_next(request)
            
            return response
            
        except Exception as e:
            logger.error(f"Tenant context middleware error: {e}")
            raise HTTPException(500, "Internal server error")
    
    async def _set_org_context(self, request: Request, organization_id: str):
        """Set PostgreSQL session variable for RLS"""
        try:
            # Get database session from request
            db = request.app.state.db
            
            # Execute SET LOCAL (only for this transaction)
            await db.execute(
                "SELECT set_config('app.current_org_id', :org_id, false)",
                {'org_id': organization_id}
            )
            
        except Exception as e:
            logger.error(f"Failed to set org context: {e}")
            # Don't fail request, but log error
            pass


class StoreContextMiddleware(BaseHTTPMiddleware):
    """
    Optional: Set current store context
    Useful for multi-store operations
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            # Get store_id from header or query param
            store_id = request.headers.get('X-Store-ID') or request.query_params.get('store_id')
            
            if store_id:
                # Verify user has access to this store
                user = getattr(request.state, 'user', None)
                
                if user:
                    assigned_stores = user.get('assigned_stores', [])
                    can_access_all = user.get('role') in ['owner', 'admin']
                    
                    if can_access_all or store_id in assigned_stores:
                        request.state.store_id = store_id
                        logger.debug(f"Store context set: store={store_id}")
                    else:
                        logger.warning(f"User {user.get('id')} attempted to access unauthorized store {store_id}")
                        raise HTTPException(403, "Access to store denied")
            
            response = await call_next(request)
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Store context middleware error: {e}")
            raise HTTPException(500, "Internal server error")


def get_current_organization(request: Request) -> Optional[str]:
    """Helper to get current organization ID from request"""
    return getattr(request.state, 'organization_id', None)


def get_current_store(request: Request) -> Optional[str]:
    """Helper to get current store ID from request"""
    return getattr(request.state, 'store_id', None)


def require_organization(request: Request) -> str:
    """Require organization context, raise if missing"""
    org_id = get_current_organization(request)
    
    if not org_id:
        raise HTTPException(401, "Organization context required")
    
    return org_id


def require_store(request: Request) -> str:
    """Require store context, raise if missing"""
    store_id = get_current_store(request)
    
    if not store_id:
        raise HTTPException(400, "Store context required. Include X-Store-ID header or store_id param")
    
    return store_id
