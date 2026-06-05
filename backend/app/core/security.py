"""
Security utilities for JWT authentication and authorization
"""

from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis
import logging

from app.core.config import settings
from app.database import get_db_dependency
from app.models import User, UserRole

logger = logging.getLogger(__name__)

# Redis client for brute force protection
def get_redis_client():
    """Get or create Redis client for brute force tracking"""
    try:
        return redis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception as e:
        logger.warning(f"Could not connect to Redis for brute force protection: {e}")
        return None

import bcrypt

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

# Brute force protection
def check_brute_force(email: str) -> Tuple[bool, Optional[str]]:
    """
    Check if account is locked due to too many failed login attempts.
    
    Returns:
        (is_locked, message) - Tuple of whether account is locked and optional message
    """
    redis_client = get_redis_client()
    if not redis_client:
        return False, None
    
    try:
        lock_key = f"login_lock:{email}"
        failed_key = f"login_failed:{email}"
        
        # Check if account is locked
        if redis_client.exists(lock_key):
            remaining = redis_client.ttl(lock_key)
            return True, f"Account locked. Try again in {remaining} seconds"
        
        # Check failed attempts
        failed_attempts = int(redis_client.get(failed_key) or 0)
        
        return False, None
    except Exception as e:
        logger.error(f"Error checking brute force: {e}")
        return False, None

def record_failed_login(email: str) -> bool:
    """
    Record a failed login attempt and lock account if necessary.
    
    Rules:
    - Track failed attempts per email
    - Lock account after 5 failed attempts in 10 minutes
    - Return True if account should be locked
    """
    redis_client = get_redis_client()
    if not redis_client:
        return False
    
    try:
        failed_key = f"login_failed:{email}"
        lock_key = f"login_lock:{email}"
        
        # Increment failed attempts
        attempts = redis_client.incr(failed_key)
        
        # Set expiry on first attempt (10 minute window)
        if attempts == 1:
            redis_client.expire(failed_key, 600)  # 10 minutes
        
        # Lock account if 5 attempts exceeded
        if attempts >= 5:
            redis_client.setex(lock_key, 1800, "locked")  # 30 minute lock
            logger.warning(f"Account locked due to brute force: {email}")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error recording failed login: {e}")
        return False

def clear_failed_login(email: str) -> None:
    """
    Clear failed login attempts after successful authentication.
    """
    redis_client = get_redis_client()
    if not redis_client:
        return
    
    try:
        failed_key = f"login_failed:{email}"
        redis_client.delete(failed_key)
    except Exception as e:
        logger.error(f"Error clearing failed logins: {e}")

def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password meets security requirements:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Returns:
        (is_valid, error_message)
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "Password must contain at least one special character"
    
    return True, None

def sanitize_input(value: str, field_name: str = "input", max_length: int = 255) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    - Remove null bytes
    - Limit length
    - Strip whitespace
    - Check for suspicious patterns
    """
    if not value:
        return value
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Strip whitespace
    value = value.strip()
    
    # Limit length
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds maximum length of {max_length}")
    
    # Check for suspicious patterns in email-like fields
    if "@" in value:  # Likely email
        if len(value) > 254:  # RFC 5321
            raise ValueError("Email address too long")
        if value.count("@") > 1:
            raise ValueError("Email address is invalid")
    
    return value


def create_access_token(data: dict) -> str:
    """
    Create JWT access token with user_id, email, role, outlet_id, exp (24 hours)
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)  # 24 hours as requested
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """
    Verify JWT token and return decoded payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def decode_token(token: str) -> Optional[dict]:
    """
    Decode a JWT token without raising on invalid tokens.
    
    Args:
        token: Encoded JWT string (typically from Authorization: Bearer header)
        
    Returns:
        Decoded payload dict if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_dependency)
) -> User:
    """
    Dependency function that reads Bearer token, verifies it, queries User from DB, returns user object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Verify token
    payload = verify_token(token)

    # Extract user_id from token
    user_id: Optional[str] = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Query user from database
    try:
        from uuid import UUID
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await session.execute(
        select(User).where(User.user_id == user_uuid, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

def require_roles(*allowed_roles: UserRole):
    """
    Role-checking dependency factory that raises 403 if current user's role is not in allowed list

    Usage:
        @app.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_roles(UserRole.superadmin, UserRole.manager))):
            ...
    """
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[role.value for role in allowed_roles]}",
            )
        return user

    return role_checker
