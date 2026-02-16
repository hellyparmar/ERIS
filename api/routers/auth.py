"""
Authentication Router
Login, Register, Token Refresh endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import timedelta

from api.db import get_db
from api.db.multitenant_models import User
from api.auth.password import hash_password, verify_password
from api.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from api.auth.dependencies import get_current_active_user
import hashlib

# Legacy SHA256 password verification (for existing users in database)
def verify_sha256_password(plain_password: str, sha256_hash: str) -> bool:
    """Verify SHA256 hashed password"""
    return hashlib.sha256(plain_password.encode()).hexdigest() == sha256_hash

# Combined password verifier - supports both bcrypt and SHA256
def verify_password_combined(plain_password: str, stored_hash: str) -> bool:
    """Verify password - tries bcrypt first, then SHA256 as fallback"""
    # Try bcrypt first (for new passwords)
    try:
        return verify_password(plain_password, stored_hash)
    except:
        # Fall back to SHA256 (for legacy passwords in database)
        return verify_sha256_password(plain_password, stored_hash)

router = APIRouter(prefix="/auth", tags=["authentication"])

# ==================== REQUEST/RESPONSE MODELS ====================

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=200)

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: str
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# ==================== ENDPOINTS ====================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    
    - **email**: Valid email address
    - **password**: Strong password (min 8 chars)
    - **full_name**: Optional full name
    """
    # Check if email exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role="analyst",  # Default role
        organization_id=None  # TODO: Set proper organization
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with email and password
    
    Returns JWT access token and refresh token
    """
    # Find user by email using raw SQL (username field in OAuth2 form is used for email)
    from sqlalchemy import text
    
    user_email = form_data.username
    
    # Debug: Log the input
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Login attempt for: {user_email}")
    
    result = db.execute(text(
        "SELECT id, email, hashed_password FROM users WHERE email = :email LIMIT 1"
    ), {"email": user_email})
    
    user_row = result.fetchone()
    
    if not user_row:
        logger.warning(f"User not found: {user_email}")
        # Try as username instead
        result = db.execute(text(
            "SELECT id, email, hashed_password FROM users WHERE username = :username LIMIT 1"
        ), {"username": user_email})
        user_row = result.fetchone()
        
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    user_id, user_email_db, hashed_password = user_row
    logger.info(f"Found user: {user_id}, {user_email_db}")
    
    # Verify password (supports both bcrypt and SHA256 legacy passwords)
    if not verify_password_combined(form_data.password, hashed_password):
        logger.warning(f"Password verification failed for: {user_email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"Login successful for: {user_email}")
    
    # Create tokens using user ID
    access_token = create_access_token(data={"sub": str(user_id)})
    refresh_token = create_refresh_token(data={"sub": str(user_id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    """
    # Verify refresh token
    payload = verify_token(request.refresh_token)
    
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    
    # Verify user exists
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information
    
    Requires: Valid JWT token in Authorization header
    """
    return current_user

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout (client should delete token)
    
    Note: JWT tokens are stateless, so actual logout happens client-side
    In production, you might want to implement token blacklisting
    """
    return {
        "message": "Successfully logged out",
        "note": "Please delete your access and refresh tokens from client storage"
    }

@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change user password
    
    Requires authentication + correct old password
    """
    # Verify old password
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    # Validate new password
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters"
        )
    
    # Update password
    current_user.hashed_password = hash_password(new_password)
    db.commit()
    
    return {"message": "Password  changed successfully"}
