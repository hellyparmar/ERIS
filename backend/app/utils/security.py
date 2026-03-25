from datetime import datetime, timedelta
from typing import Any, Union, Optional, Set
from jose import jwt
from passlib.context import CryptContext
from app.config import settings

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory token blacklist (for logout)
# In production, this should be moved to Redis or a Database
token_blacklist: Set[str] = set()

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def blacklist_token(token: str) -> None:
    token_blacklist.add(token)

def is_token_blacklisted(token: str) -> bool:
    return token in token_blacklist

def validate_file_upload(file_size: int, content_type: str, max_size: int = 10485760, allowed_types: list = None):
    """
    Validate file upload size and type.
    Default max size: 10MB
    """
    if allowed_types is None:
        allowed_types = ["image/jpeg", "image/png", "application/pdf"]
        
    if file_size > max_size:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size allowed is {max_size/1024/1014}MB")
        
    if content_type not in allowed_types:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}")
    
    return True
