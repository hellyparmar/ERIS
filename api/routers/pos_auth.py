from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt, os, bcrypt
from dotenv import load_dotenv

from api.db import get_db

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
    Authenticate cashier with 4-digit PIN.
    Uses raw SQL to avoid ORM mapper registry conflicts.
    """
    # Fetch active cashier for this store (raw SQL — no ORM mapper)
    result = db.execute(text("""
        SELECT id, name, pin_hash, role, store_id
        FROM cashiers
        WHERE store_id = :store_id AND is_active = TRUE
        LIMIT 10
    """), {"store_id": request.store_id})
    rows = result.fetchall()

    # Find cashier whose PIN matches
    cashier = None
    for row in rows:
        try:
            if bcrypt.checkpw(request.pin.encode(), row[2].encode()):
                cashier = {"id": row[0], "name": row[1], "pin_hash": row[2], "role": row[3], "store_id": row[4]}
                break
        except Exception:
            continue

    if not cashier:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid PIN or cashier not found"
        )

    # Generate JWT token
    expires_at = datetime.utcnow() + timedelta(hours=POS_TOKEN_EXPIRY_HOURS)
    payload = {
        "cashier_id": cashier["id"],
        "cashier_name": cashier["name"],
        "role": cashier["role"],
        "store_id": cashier["store_id"],
        "exp": expires_at,
        "iat": datetime.utcnow(),
        "last_activity": datetime.utcnow().isoformat()
    }

    token = jwt.encode(payload, POS_JWT_SECRET, algorithm="HS256")

    return PINLoginResponse(
        access_token=token,
        cashier_id=cashier["id"],
        cashier_name=cashier["name"],
        role=cashier["role"],
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
