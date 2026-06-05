"""
JWT Authentication Router for Enterprise Retail Intelligence System

FastAPI router with authentication endpoints:
- POST /login: Authenticate user and return JWT token
- POST /logout: Logout (client-side token management)
- GET /me: Get current user profile
- PUT /change-password: Change user password
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database import get_db_dependency
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_roles
)
from app.models import User, UserRole

# Pydantic models for request/response
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class UserProfile(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    role: UserRole
    outlet_id: str | None
    is_active: bool
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class MessageResponse(BaseModel):
    message: str

# Create router
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_db_dependency)
) -> LoginResponse:
    """
    Authenticate user with email/password and return JWT token

    Updates last_login timestamp on successful authentication
    """
    # Query user by email
    result = await session.execute(
        select(User).where(User.email == request.email, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last_login
    await session.execute(
        update(User)
        .where(User.user_id == user.user_id)
        .values(last_login=datetime.utcnow())
    )
    await session.commit()

    # Create JWT token with required payload
    token_data = {
        "user_id": str(user.user_id),
        "email": user.email,
        "role": user.role.value,  # Convert enum to string
        "outlet_id": str(user.outlet_id) if user.outlet_id else None,
    }
    access_token = create_access_token(token_data)

    # Return response
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "user_id": str(user.user_id),
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "outlet_id": str(user.outlet_id) if user.outlet_id else None,
        }
    )

@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user)
) -> MessageResponse:
    """
    Logout user

    In a stateless JWT system, logout is handled client-side by discarding the token.
    In production, you might want to implement token blacklisting.
    """
    # Client handles token deletion, server just confirms
    return MessageResponse(message="Successfully logged out")

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserProfile:
    """
    Get full current user profile
    """
    return UserProfile(
        user_id=str(current_user.user_id),
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        outlet_id=str(current_user.outlet_id) if current_user.outlet_id else None,
        is_active=current_user.is_active,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )

@router.put("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_dependency)
) -> MessageResponse:
    """
    Change user password

    Requires current password verification before allowing change
    """
    # Verify current password
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Hash new password
    new_password_hash = hash_password(request.new_password)

    # Update password in database
    await session.execute(
        update(User)
        .where(User.user_id == current_user.user_id)
        .values(password_hash=new_password_hash)
    )
    await session.commit()

    return MessageResponse(message="Password changed successfully")