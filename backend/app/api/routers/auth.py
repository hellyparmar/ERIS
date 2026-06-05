"""
Authentication Router
Login, Register, Token Refresh endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import timedelta

from app.api.db import get_db
from app.models.multitenant_models import User
from app.api.auth.password import hash_password, verify_password
from app.api.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.api.auth.dependencies import get_current_active_user
import hashlib
import re
from datetime import datetime, timezone, timedelta
from app.api.utils.audit import log_audit_action
from fastapi import Request

# Password Complexity Regex (Min 8, 1 uppercase, 1 lowercase, 1 number, 1 special character)
PASSWORD_COMPLEXITY_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$')

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
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_email = result.scalar_one_or_none()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength strictly
    if not PASSWORD_COMPLEXITY_REGEX.match(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least 8 characters, one uppercase, one lowercase, one number, and one special character"
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
    request: Request,
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
    
    # Find user object to check for lockout and manage failed attempts
    result = await db.execute(select(User).where(User.id == user_id))
    user_obj = result.scalar_one_or_none()
    if user_obj:
        # Check if account is currently locked
        if user_obj.locked_until and user_obj.locked_until > datetime.now(timezone.utc):
            logger.warning(f"Login attempt on locked account: {user_email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account locked due to too many failed attempts. Try again later."
            )
            
    # Verify password (supports both bcrypt and SHA256 legacy passwords)
    if not verify_password_combined(form_data.password, hashed_password):
        logger.warning(f"Password verification failed for: {user_email}")
        
        # Increment failed login attempts if user exists
        if user_obj:
            user_obj.failed_login_attempts = (user_obj.failed_login_attempts or 0) + 1
            if user_obj.failed_login_attempts >= 5:
                # Lock the account for 15 minutes
                user_obj.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
                logger.warning(f"Account locked after 5 failed attempts: {user_email}")
                # Audit the lockout
                log_audit_action(
                    db=db,
                    action="LOGIN_FAILED_LOCKOUT",
                    table_name="users",
                    record_id=str(user_id),
                    user_id=user_id,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent")
                )
            db.commit()
            
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Reset failed login attempts on successful login
    if user_obj:
        user_obj.failed_login_attempts = 0
        user_obj.locked_until = None
        db.commit()
        
    logger.info(f"Login successful for: {user_email}")
    
    # Audit successful login
    log_audit_action(
        db=db,
        action="LOGIN_SUCCESS",
        table_name="users",
        record_id=str(user_id),
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
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
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
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
    request: Request,
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
    
    # Validate new password strictly
    if not PASSWORD_COMPLEXITY_REGEX.match(new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must contain at least 8 characters, one uppercase, one lowercase, one number, and one special character"
        )
    
    # Update password
    current_user.hashed_password = hash_password(new_password)
    db.commit()
    
    # Audit the password change
    log_audit_action(
        db=db,
        action="CHANGE_PASSWORD",
        table_name="users",
        record_id=str(current_user.id),
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    return {"message": "Password  changed successfully"}
