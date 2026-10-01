"""
CANONICAL SECURITY MODULE — app.core.security
==============================================
This is the single, authoritative source of security and authentication
utilities for the ERIS backend. Do NOT create parallel security modules.

Past duplicates that have been removed:
  - backend/app/utils/security.py          (deleted; had in-memory token_blacklist)
  - backend/app/api/utils/auth.py          (deleted; had hardcoded SECRET_KEY fallback
                                            and a fake in-memory users DB)

Provided API
------------
  hash_password(password)          -> str     bcrypt hash (rounds=12)
  verify_password(plain, hashed)   -> bool    bcrypt verify
  create_access_token(data, ...)   -> str     HS256 JWT, ACCESS_TOKEN_EXPIRE_MINUTES expiry
  create_refresh_token(data, ...)  -> str     HS256 JWT, REFRESH_TOKEN_EXPIRE_DAYS expiry
  verify_token(token)              -> dict    decodes or raises 401
  decode_token(token)              -> dict|None  decodes without raising
  validate_password_strength(pw)   -> (bool, str|None)
  sanitize_input(value, ...)       -> str
Authentication dependencies live only in app.api.deps.
"""

from datetime import datetime, timedelta
import logging
from typing import Optional, Tuple

import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


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
    value = value.replace("\x00", "")

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


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token with user_id, email, role, outlet_id, exp.
    Honors settings.ACCESS_TOKEN_EXPIRE_MINUTES unless explicit expires_delta is passed.
    """
    to_encode = data.copy()
    if expires_delta is not None:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT refresh token with longer expiration.
    Honors settings.REFRESH_TOKEN_EXPIRE_DAYS unless explicit expires_delta is passed.
    """
    to_encode = data.copy()
    if expires_delta is not None:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
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
