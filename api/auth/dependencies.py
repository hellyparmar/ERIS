"""
Authentication Dependencies
Reusable dependencies for route protection
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional

from api.db.database import get_db
from api.db.models import User
from api.auth.jwt_handler import decode_access_token

# OAuth2 scheme (tells FastAPI where to look for token)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False  # Don't auto-error, we'll handle it
)

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current authenticated user from JWT token
    
    Args:
        token: JWT token from Authorization header
        db: Database session
    
    Returns:
        User object if authenticated, None otherwise
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    if token is None:
        return None
    
    # Decode token
    user_id = decode_access_token(token)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (requires authentication)
    
    Args:
        current_user: User from get_current_user
    
    Returns:
        User object
    
    Raises:
        HTTPException: If not authenticated
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current admin user (requires admin role)
    
    Args:
        current_user: Authenticated user
    
    Returns:
        Admin user object
    
    Raises:
        HTTPException: If not admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin access required."
        )
    
    return current_user

def optional_authentication(
    current_user: Optional[User] = Depends(get_current_user)
) -> Optional[User]:
    """
    Optional authentication (doesn't require login)
    Useful for features that work differently when logged in
    
    Args:
        current_user: User if authenticated, None otherwise
    
    Returns:
        User object or None
    """
    return current_user
