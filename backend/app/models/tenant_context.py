"""
Phase 6 - Task 2: Tenant Context Manager
Extract and manage tenant context from JWT tokens for row-level security
"""

from fastapi import Request, HTTPException, status
from typing import Optional
import uuid
import logging
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from datetime import datetime

logger = logging.getLogger(__name__)

class TenantContext:
    """
    Tenant context extracted from JWT token
    Ensures all database queries are scoped to the current tenant
    """
    
    def __init__(self, tenant_id: uuid.UUID, user_id: uuid.UUID, user_role: str, store_id: Optional[uuid.UUID] = None):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.user_role = user_role
        self.store_id = store_id
        self.extracted_at = datetime.utcnow()
    
    def __repr__(self):
        return f"<TenantContext tenant={self.tenant_id} user={self.user_id} role={self.user_role}>"


class TenantContextManager:
    """
    Manages tenant context extraction and validation
    Ensures requests are properly scoped to their tenant
    """
    
    # Store tenant context in request state
    _context_key = "tenant_context"
    
    @staticmethod
    async def extract_from_request(request: Request) -> TenantContext:
        """
        Extract tenant context from JWT token in request headers
        
        JWT payload should contain:
        - tenant_id: UUID of the organization
        - user_id: UUID of the user
        - user_role: Role of the user (admin, manager, cashier, etc.)
        - store_id: (optional) UUID of the store
        """
        try:
            # Get token from Authorization header
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing or invalid Authorization header"
                )
            
            token = auth_header.split(" ")[1]
            
            # Decode JWT (use your JWT_SECRET_KEY)
            import os
            jwt_secret = os.getenv("JWT_SECRET_KEY", "your-secret-key")
            
            payload = decode(token, jwt_secret, algorithms=["HS256"])
            
            # Extract tenant context from payload
            tenant_id = payload.get("tenant_id")
            user_id = payload.get("user_id") or payload.get("sub")
            user_role = payload.get("role", "user")
            store_id = payload.get("store_id")
            
            if not tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Token missing tenant_id claim"
                )
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Token missing user_id claim"
                )
            
            # Convert to UUIDs
            try:
                tenant_id = uuid.UUID(str(tenant_id))
                user_id = uuid.UUID(str(user_id))
                if store_id:
                    store_id = uuid.UUID(str(store_id))
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid UUID format in token: {e}"
                )
            
            # Create and store context
            context = TenantContext(tenant_id, user_id, user_role, store_id)
            request.state.tenant_context = context
            
            logger.debug(f"Extracted tenant context: {context}")
            return context
            
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Error extracting tenant context: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extract tenant context"
            )
    
    @staticmethod
    def get_from_request(request: Request) -> Optional[TenantContext]:
        """Get tenant context from request state"""
        return getattr(request.state, "tenant_context", None)
    
    @staticmethod
    def get_tenant_id(request: Request) -> uuid.UUID:
        """Get tenant_id from request - raises 401 if not found"""
        context = TenantContextManager.get_from_request(request)
        if not context:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant context not found"
            )
        return context.tenant_id
    
    @staticmethod
    def get_user_id(request: Request) -> uuid.UUID:
        """Get user_id from request - raises 401 if not found"""
        context = TenantContextManager.get_from_request(request)
        if not context:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant context not found"
            )
        return context.user_id
    
    @staticmethod
    def get_store_id(request: Request) -> Optional[uuid.UUID]:
        """Get store_id from request - can be None"""
        context = TenantContextManager.get_from_request(request)
        if not context:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant context not found"
            )
        return context.store_id
    
    @staticmethod
    def verify_tenant_access(request: Request, resource_tenant_id: uuid.UUID) -> bool:
        """
        Verify that the current user has access to the given tenant
        Raises 403 Forbidden if access is denied
        """
        context = TenantContextManager.get_from_request(request)
        if not context:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant context not found"
            )
        
        if context.tenant_id != resource_tenant_id:
            logger.warning(
                f"Unauthorized tenant access attempt: user {context.user_id} "
                f"from tenant {context.tenant_id} trying to access tenant {resource_tenant_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this resource"
            )
        
        return True


class TenantFilterMixin:
    """
    Mixin for queries to automatically apply tenant filters
    
    Usage:
    ```python
    from app.api.db.tenant_context import TenantFilterMixin
    
    query = session.query(User).filter(User.tenant_id == tenant_id)
    # OR use helper:
    query = TenantFilterMixin.apply_tenant_filter(query, User, tenant_id)
    ```
    """
    
    @staticmethod
    def apply_tenant_filter(query, model_class, tenant_id: uuid.UUID):
        """
        Apply tenant filter to a SQLAlchemy query
        """
        if not hasattr(model_class, 'tenant_id'):
            logger.warning(f"Model {model_class.__name__} does not have tenant_id column")
            return query
        
        return query.filter(model_class.tenant_id == tenant_id)
    
    @staticmethod
    def ensure_tenant_column(model_class) -> bool:
        """Check if model has tenant_id column"""
        return hasattr(model_class, 'tenant_id')


# FastAPI dependency for automatic tenant extraction
async def get_tenant_context(request: Request) -> TenantContext:
    """
    FastAPI dependency to extract and provide tenant context
    
    Usage in endpoints:
    ```python
    @app.get("/api/v1/users")
    async def list_users(tenant: TenantContext = Depends(get_tenant_context)):
        # tenant.tenant_id, tenant.user_id, tenant.user_role available
        pass
    ```
    """
    return await TenantContextManager.extract_from_request(request)


# Tenant-aware query builder
class TenantAwareQuery:
    """
    Helper class to build tenant-aware queries safely
    """
    
    def __init__(self, session, model_class, tenant_id: uuid.UUID):
        self.session = session
        self.model_class = model_class
        self.tenant_id = tenant_id
        
        if not TenantFilterMixin.ensure_tenant_column(model_class):
            raise ValueError(f"{model_class.__name__} does not support multi-tenancy")
        
        self.query = session.query(model_class).filter(
            model_class.tenant_id == tenant_id
        )
    
    def filter(self, *args, **kwargs):
        """Add additional filters"""
        self.query = self.query.filter(*args, **kwargs)
        return self
    
    def all(self):
        """Execute and return all results"""
        return self.query.all()
    
    def first(self):
        """Execute and return first result"""
        return self.query.first()
    
    def count(self):
        """Count results"""
        return self.query.count()
    
    def get(self, id):
        """Get by ID"""
        return self.query.filter(self.model_class.id == id).first()
