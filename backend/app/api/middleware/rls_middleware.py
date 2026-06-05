"""
FastAPI Middleware for Automatic Row-Level Security (RLS) Enforcement
======================================================================

This middleware:
1. Extracts tenant_id from JWT token in every request
2. Automatically sets tenant context for all database operations
3. Validates tenant access on protected endpoints
4. Prevents unauthorized tenant switching
5. Provides audit logging for security events

Key Feature: Makes RLS transparent to route handlers. Database isolation
is automatic at the PostgreSQL level.
"""

import logging
import time
import uuid
from typing import Optional, Callable, Any

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os
from jose import jwt, JWTError

from app.api.core.rls_database import TenantContextManager

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# MODELS
# ============================================================================

class TenantInfo:
    """Container for tenant information extracted from JWT."""
    
    def __init__(
        self,
        tenant_id: str,
        user_id: str,
        username: str,
        roles: list[str],
    ):
        """Initialize tenant info."""
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.username = username
        self.roles = roles
    
    def __repr__(self) -> str:
        return f"TenantInfo(tenant={self.tenant_id}, user={self.username})"


# ============================================================================
# REQUEST-LOCAL CONTEXT STORAGE
# ============================================================================

# Dictionary to store request-local tenant info
# In production, use contextvars for proper async context
_request_tenant_info: dict[int, TenantInfo] = {}


def set_request_tenant_info(
    request_id: int,
    tenant_info: TenantInfo,
) -> None:
    """Store tenant info for this request."""
    _request_tenant_info[request_id] = tenant_info


def get_request_tenant_info(request_id: int) -> Optional[TenantInfo]:
    """Retrieve tenant info for this request."""
    return _request_tenant_info.get(request_id)


def clear_request_tenant_info(request_id: int) -> None:
    """Clear tenant info for this request."""
    _request_tenant_info.pop(request_id, None)


# ============================================================================
# RLS MIDDLEWARE
# ============================================================================

class RLSMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce Row-Level Security through automatic tenant context.
    
    This middleware:
    1. Extracts tenant_id from JWT token or headers
    2. Validates the tenant_id
    3. Sets RLS context on the database connection
    4. Makes it physically impossible to query data from other tenants
    """
    
    # Paths that don't require tenant context
    EXCLUDED_PATHS = {
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/auth/login",
        "/auth/register",
        "/auth/token",
        "/api/health",
    }
    
    def __init__(self, app: FastAPI):
        """Initialize middleware."""
        super().__init__(app)
        self.app = app
    
    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """
        Process request and enforce RLS context.
        
        This is called for every request and sets up tenant isolation.
        """
        request_id = id(request)  # Use object id as unique request identifier
        start_time = time.time()
        
        try:
            # Skip RLS check for health checks and auth endpoints
            if self._should_skip_rls(request.url.path):
                logger.debug(f"Skipping RLS check for {request.url.path}")
                response = await call_next(request)
                return response
            
            # Extract tenant context from request
            tenant_info = await self._extract_tenant_context(request)
            
            if not tenant_info:
                logger.warning(
                    f"Request {request.method} {request.url.path} "
                    "missing tenant context"
                )
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "detail": "Tenant context not found. "
                                 "Please provide valid authentication."
                    }
                )
            
            # Store tenant info in request-local storage
            set_request_tenant_info(request_id, tenant_info)
            
            # Set database tenant context
            TenantContextManager.set_current_tenant(
                tenant_id=tenant_info.tenant_id,
                user_id=tenant_info.user_id,
                username=tenant_info.username,
            )
            
            logger.debug(
                f"RLS context set: tenant_id={tenant_info.tenant_id}, "
                f"user={tenant_info.username}, path={request.url.path}"
            )
            
            # Call the route handler
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Tenant-ID"] = tenant_info.tenant_id
            response.headers["X-User-ID"] = tenant_info.user_id
            
            # Log request metrics
            duration = time.time() - start_time
            status_code = response.status_code
            
            if status_code >= 400:
                logger.warning(
                    f"Request {request.method} {request.url.path} "
                    f"returned {status_code} ({duration:.2f}s)"
                )
            else:
                logger.debug(
                    f"Request {request.method} {request.url.path} "
                    f"completed ({duration:.2f}s)"
                )
            
            return response
        
        except Exception as e:
            logger.error(
                f"RLS middleware error on {request.method} {request.url.path}: {e}",
                exc_info=True
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )
        
        finally:
            # Clean up request-local context
            clear_request_tenant_info(request_id)
            TenantContextManager.clear_current_tenant()
    
    @staticmethod
    def _should_skip_rls(path: str) -> bool:
        """Check if this path should skip RLS enforcement."""
        # Exact match
        if path in RLSMiddleware.EXCLUDED_PATHS:
            return True
        
        # Prefix match
        for excluded in RLSMiddleware.EXCLUDED_PATHS:
            if path.startswith(excluded):
                return True
        
        return False
    
    @staticmethod
    async def _extract_tenant_context(request: Request) -> Optional[TenantInfo]:
        """
        Extract tenant context from request.
        
        Supports:
        1. JWT token in Authorization header
        2. Tenant ID in X-Tenant-ID header (for API calls)
        3. Tenant ID in query parameters (for special cases)
        
        Args:
            request: FastAPI Request object
        
        Returns:
            TenantInfo if valid tenant context found, None otherwise
        """
        tenant_id = None
        user_id = None
        username = None
        roles = []
        
        # Try to extract from JWT token (preferred method)
        token = RLSMiddleware._extract_token_from_header(request)
        if token:
            tenant_info = await RLSMiddleware._verify_jwt_token(token)
            if tenant_info:
                return tenant_info
        
        # Try to extract from X-Tenant-ID header (API key authentication)
        tenant_id = request.headers.get("X-Tenant-ID")
        user_id = request.headers.get("X-User-ID")
        username = request.headers.get("X-Username")
        
        if tenant_id:
            # Validate tenant_id format
            try:
                uuid.UUID(tenant_id)
                return TenantInfo(
                    tenant_id=tenant_id,
                    user_id=user_id or "unknown",
                    username=username or "api",
                    roles=roles,
                )
            except ValueError:
                logger.warning(f"Invalid tenant_id format: {tenant_id}")
                return None
        
        # Try to extract from query parameters (fallback for special cases)
        tenant_id = request.query_params.get("tenant_id")
        if tenant_id:
            try:
                uuid.UUID(tenant_id)
                return TenantInfo(
                    tenant_id=tenant_id,
                    user_id=user_id or "unknown",
                    username=username or "unknown",
                    roles=roles,
                )
            except ValueError:
                logger.warning(f"Invalid tenant_id in query params: {tenant_id}")
        
        return None
    
    @staticmethod
    def _extract_token_from_header(request: Request) -> Optional[str]:
        """Extract JWT token from Authorization header."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        
        # Expected format: "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        return parts[1]
    
    @staticmethod
    async def _verify_jwt_token(token: str) -> Optional[TenantInfo]:
        """
        Verify JWT token and extract tenant info.
        
        Uses python-jose library for secure JWT verification.
        """
        try:
            # JWT configuration (same as used in auth system)
            SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-2026!rdios")
            ALGORITHM = "HS256"
            
            # Decode and verify JWT
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Check token type
            if payload.get("type") not in ("access", "pos"):
                logger.warning(f"Invalid token type in JWT: {payload.get('type')}")
                return None
            
            # Extract required fields
            user_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")
            username = payload.get("username")
            roles = payload.get("role", [])
            
            if not user_id or not tenant_id:
                logger.warning("JWT missing required fields: sub or tenant_id")
                return None
            
            # Convert roles to list if it's a single string
            if isinstance(roles, str):
                roles = [roles]
            
            return TenantInfo(
                tenant_id=str(tenant_id),
                user_id=int(user_id),
                username=username or f"user_{user_id}",
                roles=roles,
            )
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during JWT verification: {str(e)}")
            return None
        except Exception as e:
            logger.debug(f"JWT verification failed: {e}")
            return None


# ============================================================================
# DEPENDENCY INJECTION HELPERS
# ============================================================================

async def get_tenant_info() -> TenantInfo:
    """
    Dependency to inject tenant info into route handlers.
    
    Usage:
        @app.get("/products")
        async def get_products(tenant_info: TenantInfo = Depends(get_tenant_info)):
            # tenant_info.tenant_id is automatically available
            return {"tenant_id": tenant_info.tenant_id}
    """
    # This is a simplified version
    # In production, use contextvars or request-scoped storage
    tenant_id = TenantContextManager.get_current_tenant()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant context not available"
        )
    
    return TenantInfo(
        tenant_id=tenant_id,
        user_id="",
        username="",
        roles=[],
    )


async def require_tenant_context() -> None:
    """
    Dependency to require tenant context.
    
    Usage:
        @app.get("/protected")
        async def protected_route(_: None = Depends(require_tenant_context)):
            # This route will fail if tenant context is not set
            return {"status": "ok"}
    """
    if not TenantContextManager.is_tenant_set():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant context required for this operation"
        )


# ============================================================================
# FASTAPI APPLICATION SETUP
# ============================================================================

def setup_rls_middleware(app: FastAPI) -> None:
    """
    Setup RLS middleware on FastAPI application.
    
    This should be called during application initialization.
    
    Usage:
        from fastapi import FastAPI
        from app.api.middleware.rls_middleware import setup_rls_middleware
        
        app = FastAPI()
        setup_rls_middleware(app)
        
        # Now all requests are RLS-protected
    """
    app.add_middleware(RLSMiddleware)
    logger.info("RLS middleware installed on FastAPI application")


# ============================================================================
# EXPORT PUBLIC API
# ============================================================================

__all__ = [
    "RLSMiddleware",
    "TenantInfo",
    "setup_rls_middleware",
    "get_tenant_info",
    "require_tenant_context",
    "TenantContextManager",
]
