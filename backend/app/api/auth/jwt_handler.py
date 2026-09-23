"""
JWT Token Handler
Generate and validate JWT tokens for authentication
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt

from app.core.config import settings

# Configuration
ALGORITHM = getattr(settings, "JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 15)
REFRESH_TOKEN_EXPIRE_DAYS = getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 30)

def get_secret_key():
    return getattr(settings, "JWT_SECRET_KEY", "your-secret-key-change-in-production-immediately")

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Payload to encode (typically {"sub": user_id})
        expires_delta: Custom expiration time
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT refresh token (longer expiration)
    
    Args:
        data: Payload to encode
        expires_delta: Optional custom timedelta
    
    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    if expires_delta is not None:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict]:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def decode_access_token(token: str) -> Optional[str]:
    """
    Decode access token and extract user ID
    
    Args:
        token: JWT access token
    
    Returns:
        User ID (sub claim) if valid, None otherwise
    """
    payload = verify_token(token)
    
    if payload is None:
        return None
    
    # Check if user_id is present directly (from auth.py format)
    if "user_id" in payload:
        return str(payload["user_id"])
        
    # Verify it's an access token (from jwt_handler.py format)
    if payload.get("type") == "access":
        user_id: str = payload.get("sub")
        return user_id
        
    sub = payload.get("sub")
    if sub and str(sub).isdigit():
        return str(sub)
        
    return None

def is_token_expired(token: str) -> bool:
    """
    Check if token is expired
    
    Args:
        token: JWT token
    
    Returns:
        True if expired, False if valid
    """
    payload = verify_token(token)
    
    if payload is None:
        return True
    
    exp = payload.get("exp")
    if exp is None:
        return True
    
    return datetime.utcnow() > datetime.fromtimestamp(exp)
