"""
POS Authentication Router
Cashier PIN login with JWT tokens
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv

from api.db import get_db
from api.models.cashier import Cashier

load_dotenv('backend/.env')

router = APIRouter(prefix="/auth/pos", tags=["POS Authentication"])
security = HTTPBearer()

# JWT Configuration
POS_JWT_SECRET = os.getenv("POS_JWT_SECRET", "change-this-in-production-pos-secret-key")
POS_TOKEN_EXPIRY_HOURS = int(os.getenv("POS_TOKEN_EXPIRY_HOURS", "8"))
POS_IDLE_TIMEOUT_MINUTES = int(os.getenv("POS_IDLE_TIMEOUT_MINUTES", "30"))

class PINLoginRequest(BaseModel):
    pin: str
    store_id: int

class PINLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    cashier_id: int
    cashier_name: str
    role: str
    expires_at: datetime

@router.post("/login", response_model=PINLoginResponse)
async def pos_login(request: PINLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate cashier with 4-digit PIN
    Returns JWT token valid for 8 hours
    """
    # Find active cashier by store
    cashier = db.query(Cashier).filter(
        Cashier.store_id == request.store_id,
        Cashier.is_active == True
    ).first()
    
    if not cashier or not cashier.verify_pin(request.pin):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid PIN or cashier not found"
        )
    
    # Generate JWT token
    expires_at = datetime.utcnow() + timedelta(hours=POS_TOKEN_EXPIRY_HOURS)
    payload = {
        "cashier_id": cashier.id,
        "cashier_name": cashier.name,
        "role": cashier.role,
        "store_id": cashier.store_id,
        "exp": expires_at,
        "iat": datetime.utcnow(),
        "last_activity": datetime.utcnow().isoformat()
    }
    
    token = jwt.encode(payload, POS_JWT_SECRET, algorithm="HS256")
    
    return PINLoginResponse(
        access_token=token,
        cashier_id=cashier.id,
        cashier_name=cashier.name,
        role=cashier.role,
        expires_at=expires_at
    )

@router.post("/refresh")
async def pos_refresh(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Refresh token on activity (reset 30min idle timeout)
    """
    try:
        payload = jwt.decode(credentials.credentials, POS_JWT_SECRET, algorithms=["HS256"])
        
        # Check idle timeout
        last_activity = datetime.fromisoformat(payload.get("last_activity", datetime.utcnow().isoformat()))
        if datetime.utcnow() - last_activity > timedelta(minutes=POS_IDLE_TIMEOUT_MINUTES):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired due to inactivity"
            )
        
        # Update last activity
        payload["last_activity"] = datetime.utcnow().isoformat()
        new_token = jwt.encode(payload, POS_JWT_SECRET, algorithm="HS256")
        
        return {"access_token": new_token, "token_type": "bearer"}
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@router.post("/logout")
async def pos_logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout cashier (client should delete token)
    """
    return {"message": "Logged out successfully"}

def verify_pos_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to verify POS JWT token
    Use in protected routes: Depends(verify_pos_token)
    """
    try:
        payload = jwt.decode(credentials.credentials, POS_JWT_SECRET, algorithms=["HS256"])
        
        # Check idle timeout
        last_activity = datetime.fromisoformat(payload.get("last_activity", datetime.utcnow().isoformat()))
        if datetime.utcnow() - last_activity > timedelta(minutes=POS_IDLE_TIMEOUT_MINUTES):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired due to inactivity"
            )
        
        return payload
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
