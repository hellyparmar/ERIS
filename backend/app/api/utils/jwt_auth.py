"""
JWT Authentication for R-DIOS v3.0
Implements TWO flows: Manager/Admin (password) + Cashier (PIN)
"""

import os
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-2026!rdios")
POS_SECRET = os.getenv("POS_JWT_SECRET", "pos-secret-key-change-in-production!rdios")
ALGORITHM = "HS256"
PIN_SALT = os.getenv("PIN_SALT", "rdios-pin-salt")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()

# Permission matrix
PERMISSIONS = {
    "cashier": [
        "pos.sell",
        "pos.view_products",
        "pos.view_own_shift"
    ],
    "manager": [
        "pos.sell",
        "pos.refund",
        "pos.discount_override",
        "pos.price_override",
        "inventory.view",
        "inventory.edit",
        "reports.view",
        "customers.view",
        "customers.edit",
        "alerts.manage"
    ],
    "accountant": [
        "reports.view",
        "reports.export",
        "invoices.view",
        "invoices.create",
        "gst.export",
        "tally.sync",
        "suppliers.view"
    ],
    "admin": ["*"]
}

# ═══════════════════════════════════════════════════════════════
# FLOW 1: Manager/Admin — Password + JWT (1-hour expiry)
# ═══════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(
    user_id: int,
    role: str,
    tenant_id: int,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create access token for manager/admin"""
    if expires_delta is None:
        expires_delta = timedelta(hours=1)
    
    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "sub": str(user_id),
        "role": role,
        "tenant_id": tenant_id,
        "type": "access",
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(user_id: int) -> str:
    """Create refresh token (30-day expiry)"""
    expire = datetime.utcnow() + timedelta(days=30)
    to_encode = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_access_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> Dict[str, Any]:
    """Verify access token and return payload"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") not in ("access", "pos"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return {
            "user_id": int(user_id),
            "role": payload.get("role"),
            "tenant_id": payload.get("tenant_id"),
            "token_type": payload.get("type")
        }
    
    except JWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

def require_role(*allowed_roles):
    """Dependency to require specific roles"""
    async def check_role(current_user: Dict = Depends(verify_access_token)):
        role = current_user.get("role")
        perms = PERMISSIONS.get(role, [])
        
        # Admin has all permissions
        if "*" in perms:
            return current_user
        
        # Check if role is in allowed list
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {allowed_roles}, Got: {role}"
            )
        
        return current_user
    
    return check_role

def require_permission(*required_permissions):
    """Dependency to require specific permissions"""
    async def check_permission(current_user: Dict = Depends(verify_access_token)):
        role = current_user.get("role")
        perms = PERMISSIONS.get(role, [])
        
        # Admin has all permissions
        if "*" in perms:
            return current_user
        
        # Check if any required permission is granted
        has_permission = any(p in perms for p in required_permissions)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {required_permissions}"
            )
        
        return current_user
    
    return check_permission

# ═══════════════════════════════════════════════════════════════
# FLOW 2: Cashier — PIN + JWT (8-hour expiry)
# ═══════════════════════════════════════════════════════════════

def hash_pin(pin: str) -> str:
    """Hash PIN using SHA256 with salt"""
    return hashlib.sha256(f"{PIN_SALT}{pin}".encode()).hexdigest()

def verify_pin(pin: str, stored_hash: str) -> bool:
    """Verify PIN against stored hash"""
    return hash_pin(pin) == stored_hash

def create_pos_token(
    employee_id: int,
    employee_name: str,
    role: str,
    tenant_id: int
) -> str:
    """Create POS token for cashier (8-hour expiry)"""
    expire = datetime.utcnow() + timedelta(hours=8)
    to_encode = {
        "sub": str(employee_id),
        "name": employee_name,
        "role": role,
        "tenant_id": tenant_id,
        "type": "pos",
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(to_encode, POS_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_pos_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> Dict[str, Any]:
    """Verify POS token and return payload"""
    try:
        payload = jwt.decode(credentials.credentials, POS_SECRET, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != "pos":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type — expected POS token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        employee_id: str = payload.get("sub")
        if employee_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return {
            "employee_id": int(employee_id),
            "employee_name": payload.get("name"),
            "role": payload.get("role"),
            "tenant_id": payload.get("tenant_id"),
            "token_type": "pos"
        }
    
    except JWTError as e:
        logger.error(f"POS token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired POS token",
            headers={"WWW-Authenticate": "Bearer"}
        )

# ═══════════════════════════════════════════════════════════════
# Manager Override (for high-value transactions)
# ═══════════════════════════════════════════════════════════════

def verify_manager_override(manager_id: int, manager_pin: str, manager_pin_hash: str) -> bool:
    """Verify manager PIN for override approval"""
    return verify_pin(manager_pin, manager_pin_hash)
