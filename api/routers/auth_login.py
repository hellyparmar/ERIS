"""
Authentication endpoints for R-DIOS API
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from api.utils.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    fake_users_db,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    User,
    Token
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint - Returns JWT access token
    
    Test credentials:
    - username: admin, password: secret
    - username: user, password: secret
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information
    Requires valid JWT token
    """
    return current_user

@router.get("/status")
async def auth_status():
    """
    Check authentication service status
    """
    return {
        "status": "active",
        "service": "JWT Authentication",
        "version": "1.0",
        "test_credentials": {
            "username": "admin or user",
            "password": "secret"
        }
    }
