"""
backend/app/auth/auth.py
Core JWT + password utilities — clean public API for the auth system.

FEATURES:
- Password hashing with bcrypt
- JWT token generation (access + refresh)
- Token validation and decoding
- Password strength validation (8+ chars, 1 upper, 1 digit)
- FastAPI OAuth2 integration
- Refresh token database tracking for revocation

Usage:
    from app.auth.auth import (
        hash_password, verify_password,
        create_access_token, create_refresh_token,
        get_current_user, require_role,
    )
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
import bcrypt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.config import settings
from app.database import get_db

# ── Password validation ────────────────────────────────────────────────────────

# Pattern: at least 1 uppercase, 1 lowercase, 1 digit, min 8 chars
_PASSWORD_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"
)

def validate_password(password: str) -> None:
    """
    Validate password strength.
    
    Requirements:
    - At least 8 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one digit (0-9)
    
    Args:
        password: The plaintext password to validate
        
    Raises:
        ValueError: If password does not meet requirements
    """
    if not _PASSWORD_RE.match(password):
        raise ValueError(
            "Password must be at least 8 characters and include an uppercase letter, "
            "a lowercase letter, and a digit."
        )


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    
    Args:
        password: Plaintext password
        
    Returns:
        Bcrypt password hash (safe for storage)
    """
    # Truncate to 72 bytes (bcrypt limit)
    truncated = password[:72].encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(truncated, salt).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain-text password against its bcrypt hash.
    
    Args:
        plain: Plaintext password to check
        hashed: Bcrypt hash from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Truncate password to 72 bytes (bcrypt limit)
        truncated = plain[:72].encode('utf-8')
        return bcrypt.checkpw(truncated, hashed.encode('utf-8') if isinstance(hashed, str) else hashed)
    except Exception:
        return False


# ── JWT token management ───────────────────────────────────────────────────────

def create_access_token(
    user_id: Union[int, str, Any],
    extra: Optional[dict] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.
    
    Default expiry: 24 hours (from settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    Args:
        user_id: The user's primary key (embedded as 'sub' claim)
        extra: Optional additional claims to merge into payload
        expires_delta: Override default expiry (e.g., timedelta(hours=1))
        
    Returns:
        Encoded JWT string ready for Bearer token use
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict = {
        "sub": str(user_id),
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    if extra:
        payload.update(extra)
    
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    user_id: Union[int, str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT refresh token (longer-lived).
    
    Default expiry: 30 days (from settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    Args:
        user_id: The user's primary key (embedded as 'sub' claim)
        expires_delta: Override default expiry (e.g., timedelta(days=7))
        
    Returns:
        Encoded JWT string for token refresh operations
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """
    Decode a JWT token without raising on invalid tokens.
    
    Args:
        token: Encoded JWT string (typically from Authorization: Bearer header)
        
    Returns:
        Decoded payload dict if valid, None if invalid/expired
    """
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        return None


def is_token_expired(token_dict: dict) -> bool:
    """
    Check if a decoded token has expired.
    
    Args:
        token_dict: Decoded JWT payload (from decode_token)
        
    Returns:
        True if token is past its expiration time
    """
    if "exp" not in token_dict:
        return True
    
    exp_timestamp = token_dict["exp"]
    return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc) < datetime.now(timezone.utc)


# ── FastAPI OAuth2 setup ───────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    description="Bearer JWT token for API authentication"
)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

_INACTIVE_EXCEPTION = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Account is inactive or locked",
)

_LOCKED_EXCEPTION = HTTPException(
    status_code=status.HTTP_423_LOCKED,
    detail="Account is locked due to too many failed login attempts. Please try again later or contact support.",
)


# ── Token blacklist helpers ────────────────────────────────────────────────────

def is_token_blacklisted(token: str, db: Session) -> bool:
    """
    Check if a refresh token has been revoked in the database.
    
    Args:
        token: The JWT token string
        db: Database session
        
    Returns:
        True if token is blacklisted/revoked, False otherwise
    """
    from app.models.users import RefreshToken
    
    revoked = db.query(RefreshToken).filter(
        RefreshToken.token == token,
        RefreshToken.is_revoked == True
    ).first()
    
    return revoked is not None


def store_refresh_token(user_id: int, token: str, expires_at: datetime, db: Session) -> None:
    """
    Store a refresh token in the database for tracking and revocation.
    
    Args:
        user_id: User ID that owns this token
        token: The refresh token string
        expires_at: When the token expires
        db: Database session
    """
    from app.models.users import RefreshToken
    
    refresh_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
    )
    db.add(refresh_token)
    db.commit()


def revoke_refresh_token(token: str, db: Session) -> bool:
    """
    Revoke (blacklist) a refresh token.
    
    Args:
        token: The refresh token string
        db: Database session
        
    Returns:
        True if token was successfully revoked, False if not found
    """
    from app.models.users import RefreshToken
    
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token
    ).first()
    
    if not refresh_token:
        return False
    
    refresh_token.is_revoked = True
    refresh_token.revoked_at = datetime.now(timezone.utc)
    db.commit()
    
    return True


def cleanup_expired_tokens(db: Session) -> int:
    """
    Remove expired refresh tokens from the database (maintenance task).
    
    Args:
        db: Database session
        
    Returns:
        Number of expired tokens deleted
    """
    from app.models.users import RefreshToken
    
    result = db.query(RefreshToken).filter(
        RefreshToken.expires_at < datetime.now(timezone.utc)
    ).delete()
    
    db.commit()
    return result


# ── FastAPI dependency: get_current_user ───────────────────────────────────────

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    FastAPI dependency to extract and validate the current authenticated user.
    
    Validates:
    - Token signature and expiration
    - Token has 'access' type (not refresh)
    - User exists and is active
    - User account is not locked
    
    Usage in an endpoint:
        @router.get("/protected")
        async def protected_endpoint(current_user = Depends(get_current_user)):
            return {"user": current_user.email}
            
    Args:
        token: Bearer token from Authorization header (auto-extracted by oauth2_scheme)
        db: Database session
        
    Returns:
        User object if valid
        
    Raises:
        HTTPException 401: If token is invalid/expired
        HTTPException 403: If user is inactive
        HTTPException 423: If user account is locked
    """
    from app.models.users import User
    
    # Decode token
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise _CREDENTIALS_EXCEPTION
    
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise _CREDENTIALS_EXCEPTION
    
    # Fetch user
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise _CREDENTIALS_EXCEPTION
    
    # Check account status
    if not user.is_active:
        raise _INACTIVE_EXCEPTION
    
    # Check if locked
    if user.locked_until and datetime.now(timezone.utc) < user.locked_until:
        raise _LOCKED_EXCEPTION
    
    return user


# ── RBAC helper (legacy, use auth/permissions.py for new code) ────────────────

def require_role(*roles: str):
    """
    Dependency factory that restricts an endpoint to specific roles.
    
    DEPRECATED: Use require_role from auth/permissions.py instead.
    
    Usage:
        @router.delete("/items/{id}", dependencies=[Depends(require_role("admin"))])
        async def delete_item(...): ...
    """
    async def _check(current_user=Depends(get_current_user)):
        user_role = (
            current_user.role.name
            if hasattr(current_user.role, "name")
            else str(current_user.role)
        )
        if user_role.lower() not in [r.lower() for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(roles)}",
            )
        return current_user
    return _check


# Convenience aliases
require_admin = require_role("admin")
require_manager = require_role("admin", "manager")


__all__ = [
    # Password utilities
    "validate_password",
    "hash_password",
    "verify_password",
    # Token creation
    "create_access_token",
    "create_refresh_token",
    # Token validation
    "decode_token",
    "is_token_expired",
    "is_token_blacklisted",
    # Token management
    "store_refresh_token",
    "revoke_refresh_token",
    "cleanup_expired_tokens",
    # FastAPI dependencies
    "oauth2_scheme",
    "get_current_user",
    "require_role",
    "require_admin",
    "require_manager",
]

