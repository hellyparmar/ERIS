from datetime import datetime, timedelta
from typing import Optional, Union, Any
from app.utils import security

class AuthService:
    """Service for handling authentication and token generation"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        return security.verify_password(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return security.get_password_hash(password)

    @staticmethod
    def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        return security.create_access_token(subject, expires_delta)

    @staticmethod
    def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT refresh token"""
        return security.create_refresh_token(subject, expires_delta)

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Decode and validate a JWT access token"""
        from jose import jwt, JWTError
        from app.config import settings
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError:
            return None

auth_service = AuthService()
