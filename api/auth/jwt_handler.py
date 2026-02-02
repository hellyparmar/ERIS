"""
JWT Token Handler
Generate and validate JWT tokens for authentication
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-immediately")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

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
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict) -> str:
    """
    Create JWT refresh token (longer expiration)
    
    Args:
        data: Payload to encode
    
    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
    
    # Verify it's an access token
    if payload.get("type") != "access":
        return None
    
    # Extract user ID
    user_id: str = payload.get("sub")
    return user_id

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
