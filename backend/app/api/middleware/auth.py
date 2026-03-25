"""
JWT Authentication Middleware for Phase 2 APIs

Provides token-based authentication and role-based access control
"""

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from typing import Optional, Dict, List
import jwt
from datetime import datetime, timedelta
from functools import lru_cache

# Security configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30

# This should come from environment in production
SECRET_KEY = "your-super-secret-key-change-in-production"  # pragma: allowlist secret

security = HTTPBearer()


# ==================== Token Operations ====================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token
    
    Args:
        data: Token payload (should include 'sub' for subject)
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create JWT refresh token
    
    Args:
        data: Token payload
        
    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token to verify
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )


# ==================== Authentication Dependencies ====================

async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security)
) -> Dict:
    """
    Get current authenticated user from token
    
    Usage:
        @app.get("/protected")
        def protected_endpoint(user: Dict = Depends(get_current_user)):
            return {"current_user": user}
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return {
        "user_id": user_id,
        "business_id": payload.get("business_id"),
        "roles": payload.get("roles", []),
        "permissions": payload.get("permissions", []),
        "email": payload.get("email"),
        "exp": payload.get("exp")
    }


async def get_current_user_optional(
    credentials: Optional[HTTPAuthCredentials] = Depends(security)
) -> Optional[Dict]:
    """
    Get current user if authenticated, None otherwise
    
    Useful for endpoints that work both authenticated and unauthenticated
    """
    if not credentials:
        return None
    
    return await get_current_user(credentials)


# ==================== Role-Based Access Control ====================

def require_role(*roles: str):
    """
    Dependency factory for role-based access control
    
    Usage:
        @app.get("/admin-only")
        def admin_endpoint(user: Dict = Depends(require_role("admin"))):
            return {"status": "admin only"}
    
    Args:
        roles: List of allowed roles
    """
    async def check_role(user: Dict = Depends(get_current_user)) -> Dict:
        user_roles = user.get("roles", [])
        if not any(role in user_roles for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(roles)}"
            )
        return user
    
    return check_role


def require_permission(*permissions: str):
    """
    Dependency factory for permission-based access control
    
    Usage:
        @app.post("/invoice/create")
        def create_invoice(
            user: Dict = Depends(require_permission("invoice:create"))
        ):
            return {"status": "invoice created"}
    
    Args:
        permissions: List of required permissions
    """
    async def check_permission(user: Dict = Depends(get_current_user)) -> Dict:
        user_permissions = user.get("permissions", [])
        if not any(perm in user_permissions for perm in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {', '.join(permissions)}"
            )
        return user
    
    return check_permission


def require_business(required_field: str = "business_id"):
    """
    Dependency to ensure user has business_id in token
    
    Usage:
        @app.get("/api/v2/invoices")
        def list_invoices(user: Dict = Depends(require_business())):
            business_id = user.get("business_id")
            # Use business_id for data isolation
    """
    async def check_business(user: Dict = Depends(get_current_user)) -> Dict:
        if required_field not in user or not user[required_field]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {required_field}"
            )
        return user
    
    return check_business


# ==================== Authentication Models ====================

class AuthPayload:
    """Standard authentication payload"""
    
    def __init__(
        self,
        user_id: str,
        business_id: str,
        email: str = None,
        name: str = None,
        roles: List[str] = None,
        permissions: List[str] = None
    ):
        self.user_id = user_id
        self.business_id = business_id
        self.email = email
        self.name = name
        self.roles = roles or []
        self.permissions = permissions or []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for token encoding"""
        return {
            "sub": self.user_id,
            "business_id": self.business_id,
            "email": self.email,
            "name": self.name,
            "roles": self.roles,
            "permissions": self.permissions
        }


# ==================== Common Role Definitions ====================

ADMIN_ROLES = ["admin", "superadmin"]
MANAGER_ROLES = ["manager", "admin", "superadmin"]
USER_ROLES = ["user", "manager", "admin", "superadmin"]

INVOICE_PERMISSIONS = {
    "invoice:create": ["user", "manager", "admin"],
    "invoice:read": ["user", "manager", "admin"],
    "invoice:update": ["manager", "admin"],
    "invoice:delete": ["admin"],
    "invoice:pdf": ["user", "manager", "admin"]
}

CREDIT_PERMISSIONS = {
    "credit:create": ["manager", "admin"],
    "credit:read": ["user", "manager", "admin"],
    "credit:update": ["manager", "admin"],
    "credit:delete": ["admin"],
    "credit:scoring": ["manager", "admin"]
}

GST_PERMISSIONS = {
    "gst:configure": ["admin"],
    "gst:read": ["user", "manager", "admin"],
    "gst:calculate": ["user", "manager", "admin"],
    "gst:returns": ["manager", "admin"],
    "gst:compliance": ["manager", "admin"]
}


# ==================== Token Refresh ====================

def refresh_access_token(refresh_token: str) -> str:
    """
    Create new access token from refresh token
    
    Args:
        refresh_token: Valid refresh token
        
    Returns:
        New access token
    """
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Extract user data and create new access token
        user_data = {
            "sub": payload.get("sub"),
            "business_id": payload.get("business_id"),
            "email": payload.get("email"),
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", [])
        }
        
        return create_access_token(user_data)
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


# ==================== Blacklist Management ====================

# In-memory token blacklist (use Redis in production)
token_blacklist = set()


def revoke_token(token: str) -> None:
    """Revoke a token (add to blacklist)"""
    token_blacklist.add(token)


def is_token_revoked(token: str) -> bool:
    """Check if token is revoked"""
    return token in token_blacklist


# ==================== User Session Management ====================

class UserSession:
    """User session management"""
    
    # In-memory session store (use database/Redis in production)
    _sessions: Dict[str, Dict] = {}
    
    @staticmethod
    def create_session(user_id: str, business_id: str, metadata: Dict = None) -> str:
        """Create new user session"""
        import uuid
        session_id = str(uuid.uuid4())
        UserSession._sessions[session_id] = {
            "user_id": user_id,
            "business_id": business_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "metadata": metadata or {}
        }
        return session_id
    
    @staticmethod
    def get_session(session_id: str) -> Optional[Dict]:
        """Get session details"""
        session = UserSession._sessions.get(session_id)
        if session:
            session["last_activity"] = datetime.utcnow()
        return session
    
    @staticmethod
    def invalidate_session(session_id: str) -> bool:
        """Invalidate session"""
        if session_id in UserSession._sessions:
            del UserSession._sessions[session_id]
            return True
        return False
    
    @staticmethod
    def invalidate_user_sessions(user_id: str) -> int:
        """Invalidate all sessions for user"""
        sessions_to_remove = [
            sid for sid, sess in UserSession._sessions.items()
            if sess.get("user_id") == user_id
        ]
        for sid in sessions_to_remove:
            del UserSession._sessions[sid]
        return len(sessions_to_remove)


# ==================== Rate Limiting for Auth ====================

class AuthRateLimiter:
    """Rate limiter for authentication endpoints"""
    
    _attempts: Dict[str, List[datetime]] = {}
    MAX_ATTEMPTS = 5
    WINDOW_SECONDS = 300  # 5 minutes
    
    @classmethod
    def check_rate_limit(cls, identifier: str) -> bool:
        """
        Check if identifier has exceeded rate limit
        
        Args:
            identifier: Typically IP address or username
            
        Returns:
            True if within limit, False if exceeded
        """
        now = datetime.utcnow()
        
        if identifier not in cls._attempts:
            cls._attempts[identifier] = []
        
        # Remove old attempts outside window
        cls._attempts[identifier] = [
            attempt for attempt in cls._attempts[identifier]
            if (now - attempt).total_seconds() < cls.WINDOW_SECONDS
        ]
        
        # Check limit
        if len(cls._attempts[identifier]) >= cls.MAX_ATTEMPTS:
            return False
        
        # Record this attempt
        cls._attempts[identifier].append(now)
        return True
    
    @classmethod
    def reset_attempts(cls, identifier: str) -> None:
        """Reset attempts for identifier"""
        if identifier in cls._attempts:
            del cls._attempts[identifier]
