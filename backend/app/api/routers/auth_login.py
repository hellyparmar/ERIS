"""
Authentication endpoints for R-DIOS v3.0
FLOW 1: Manager/Admin password login → access_token (1 hour) + refresh_token (30 days)
FLOW 2: Cashier PIN login → pos_token (8 hours)
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from pydantic import BaseModel
from typing import Dict, Any
import logging
from datetime import timedelta
import psycopg2

from app.api.utils.jwt_auth import (
    create_access_token,
    create_refresh_token,
    create_pos_token,
    verify_password,
    hash_password,
    verify_pin,
    hash_pin,
    verify_access_token,
    verify_pos_token,
    PERMISSIONS
)
from app.api.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# ═══════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    username: str
    password: str

class POSLoginRequest(BaseModel):
    employee_id: int
    pin: str  # 4 digits

class TokenResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: str = "Login successful"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# ═══════════════════════════════════════════════════════════════
# FLOW 1: Manager/Admin Login (Password)
# ═══════════════════════════════════════════════════════════════

@router.post("/login", response_model=TokenResponse)
async def manager_login(request: LoginRequest, db=Depends(get_db)):
    """
    Manager/Admin login endpoint
    Returns: access_token (1h) + refresh_token (30d)
    
    Required: username + password
    """
    try:
        # Query user from database
        from app.api.db.models import User
        result = await db.execute(select(User).where(User.email == request.username))
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"Login attempt failed: user {request.username} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Verify password
        if not verify_password(request.password, user.password_hash or ""):
            logger.warning(f"Login attempt failed: password mismatch for {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Create tokens
        access_token = create_access_token(
            user_id=user.id,
            role=user.role or "admin",
            tenant_id=user.organization_id or 1
        )
        
        refresh_token = create_refresh_token(user.id)
        
        logger.info(f"User {user.email} ({user.role}) logged in successfully")
        
        return TokenResponse(
            success=True,
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.full_name or user.email.split("@")[0],
                    "role": user.role,
                    "permissions": PERMISSIONS.get(user.role, [])
                },
                "expires_in": 3600  # 1 hour in seconds
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

# ═══════════════════════════════════════════════════════════════
# FLOW 2: Cashier PIN Login
# ═══════════════════════════════════════════════════════════════

@router.post("/pos-login", response_model=TokenResponse)
async def cashier_login(request: POSLoginRequest, db=Depends(get_db)):
    """
    Cashier POS login endpoint
    Returns: pos_token (8 hours) for point-of-sale operations
    
    Required: employee_id + 4-digit PIN
    """
    try:
        # Validate PIN format
        if not isinstance(request.pin, str) or len(request.pin) != 4 or not request.pin.isdigit():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PIN must be 4 digits"
            )
        
        # Query employee from database
        from app.api.db.models import Employee
        result = await db.execute(select(Employee).where(Employee.id == request.employee_id))
        employee = result.scalar_one_or_none()
        
        if not employee:
            logger.warning(f"POS login attempt failed: employee {request.employee_id} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Employee ID not found"
            )
        
        if not employee.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employee account is inactive"
            )
        
        # Verify PIN
        if not verify_pin(request.pin, employee.pin_hash or ""):
            logger.warning(f"POS login attempt failed: invalid PIN for employee {request.employee_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid employee ID or PIN"
            )
        
        # Create POS token (8-hour expiry)
        pos_token = create_pos_token(
            employee_id=employee.id,
            employee_name=employee.name,
            role=employee.role or "cashier",
            tenant_id=employee.store_id or 1
        )
        
        logger.info(f"Employee {employee.name} (ID: {employee.id}) logged into POS")
        
        return TokenResponse(
            success=True,
            data={
                "token": pos_token,
                "name": employee.name,
                "role": employee.role,
                "permissions": PERMISSIONS.get(employee.role, []),
                "expires_in": 28800  # 8 hours in seconds
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"POS login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="POS login failed"
        )

# ═══════════════════════════════════════════════════════════════
# Token Refresh
# ═══════════════════════════════════════════════════════════════

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh_token
    Returns: new access_token + new refresh_token
    """
    try:
        from jose import jwt, JWTError
        from app.api.utils.jwt_auth import SECRET_KEY, ALGORITHM
        
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = int(payload.get("sub"))
        
        # Query user to get current role and tenant_id
        from app.api.db.models import User
        user = User.query.get(user_id) if hasattr(User, 'query') else None
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new tokens
        new_access_token = create_access_token(
            user_id=user.id,
            role=user.role or "admin",
            tenant_id=user.organization_id or 1
        )
        
        new_refresh_token = create_refresh_token(user.id)
        
        return TokenResponse(
            success=True,
            data={
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "expires_in": 3600
            },
            message="Token refreshed"
        )
    
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )

# ═══════════════════════════════════════════════════════════════
# Current User Info
# ═══════════════════════════════════════════════════════════════

@router.get("/me")
async def get_current_user(current_user: Dict = Depends(verify_access_token)):
    """Get current logged-in user information"""
    return {
        "success": True,
        "data": {
            "user_id": current_user["user_id"],
            "role": current_user["role"],
            "tenant_id": current_user["tenant_id"],
            "permissions": PERMISSIONS.get(current_user["role"], [])
        }
    }

@router.get("/pos/me")
async def get_pos_user(current_user: Dict = Depends(verify_pos_token)):
    """Get current POS user information"""
    return {
        "success": True,
        "data": {
            "employee_id": current_user["employee_id"],
            "name": current_user["employee_name"],
            "role": current_user["role"],
            "permissions": PERMISSIONS.get(current_user["role"], [])
        }
    }

