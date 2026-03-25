"""
Phase 6 - Admin Panel Router
User Management, Device Registry, GST Configuration
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import uuid
from app.api.db import get_db
from pydantic import BaseModel

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class UserCreate(BaseModel):
    username: str
    email: str
    role: str  # admin, manager, cashier, warehouse
    phone: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    phone: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class DeviceCreate(BaseModel):
    device_uuid: str
    device_name: str
    device_type: str  # pos, mobile, tablet
    user_id: str

class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    is_active: Optional[bool] = None

class DeviceResponse(BaseModel):
    id: str
    device_uuid: str
    device_name: str
    device_type: str
    user_id: str
    is_active: bool
    last_seen: Optional[datetime]
    created_at: datetime

class GSTRateCreate(BaseModel):
    category: str
    rate: float  # e.g., 5, 12, 18, 28
    description: Optional[str] = None
    effective_date: datetime

class GSTRateUpdate(BaseModel):
    rate: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class GSTRateResponse(BaseModel):
    id: str
    category: str
    rate: float
    description: Optional[str]
    is_active: bool
    effective_date: datetime
    created_at: datetime

class PINResetRequest(BaseModel):
    new_pin: str

# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Panel"])

# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    try:
        from sqlalchemy import text
        
        user_id = str(uuid.uuid4())
        
        # Check if email already exists
        existing = db.execute(text("""
            SELECT id FROM users WHERE email = :email LIMIT 1
        """), {"email": user.email}).fetchone()
        
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # Insert user
        db.execute(text("""
            INSERT INTO users (id, username, email, role, phone, is_active, created_at, updated_at)
            VALUES (:id, :username, :email, :role, :phone, :is_active, :created_at, :updated_at)
        """), {
            "id": user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "phone": user.phone,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        db.commit()
        
        return {
            "id": user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "phone": user.phone,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users", response_model=dict)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    role: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List users with pagination"""
    try:
        from sqlalchemy import text
        
        where_clause = "1=1"
        params = {}
        
        if role:
            where_clause += " AND role = :role"
            params["role"] = role
        
        # Get total count
        result = db.execute(text(f"""
            SELECT COUNT(*) as total FROM users WHERE {where_clause}
        """), params).fetchone()
        total = result[0] if result else 0
        
        # Get paginated results
        offset = (page - 1) * per_page
        results = db.execute(text(f"""
            SELECT id, username, email, role, phone, is_active, created_at, updated_at
            FROM users
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """), {**params, "limit": per_page, "offset": offset}).fetchall()
        
        users = [
            {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "role": row[3],
                "phone": row[4],
                "is_active": row[5],
                "created_at": row[6],
                "updated_at": row[7]
            }
            for row in results
        ]
        
        return {
            "success": True,
            "data": {
                "users": users,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}", response_model=dict)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user details"""
    try:
        from sqlalchemy import text
        
        result = db.execute(text("""
            SELECT id, username, email, role, phone, is_active, created_at, updated_at
            FROM users
            WHERE id = :user_id
        """), {"user_id": user_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "data": {
                "id": result[0],
                "username": result[1],
                "email": result[2],
                "role": result[3],
                "phone": result[4],
                "is_active": result[5],
                "created_at": result[6],
                "updated_at": result[7]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}", response_model=dict)
async def update_user(user_id: str, user: UserUpdate, db: Session = Depends(get_db)):
    """Update user details"""
    try:
        from sqlalchemy import text
        
        # Build update statement dynamically
        update_fields = []
        params = {"user_id": user_id, "updated_at": datetime.utcnow()}
        
        if user.username is not None:
            update_fields.append("username = :username")
            params["username"] = user.username
        if user.email is not None:
            update_fields.append("email = :email")
            params["email"] = user.email
        if user.role is not None:
            update_fields.append("role = :role")
            params["role"] = user.role
        if user.phone is not None:
            update_fields.append("phone = :phone")
            params["phone"] = user.phone
        if user.is_active is not None:
            update_fields.append("is_active = :is_active")
            params["is_active"] = user.is_active
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_fields.append("updated_at = :updated_at")
        
        query = f"""
            UPDATE users
            SET {', '.join(update_fields)}
            WHERE id = :user_id
        """
        
        db.execute(text(query), params)
        db.commit()
        
        # Fetch updated user
        result = db.execute(text("""
            SELECT id, username, email, role, phone, is_active, created_at, updated_at
            FROM users WHERE id = :user_id
        """), {"user_id": user_id}).fetchone()
        
        return {
            "success": True,
            "data": {
                "id": result[0],
                "username": result[1],
                "email": result[2],
                "role": result[3],
                "phone": result[4],
                "is_active": result[5],
                "created_at": result[6],
                "updated_at": result[7]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}")
async def deactivate_user(user_id: str, db: Session = Depends(get_db)):
    """Deactivate user (soft delete)"""
    try:
        from sqlalchemy import text
        
        db.execute(text("""
            UPDATE users SET is_active = FALSE, updated_at = :updated_at
            WHERE id = :user_id
        """), {"user_id": user_id, "updated_at": datetime.utcnow()})
        
        db.commit()
        
        return {"success": True, "message": "User deactivated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/{user_id}/reset-pin")
async def reset_user_pin(user_id: str, request: PINResetRequest, db: Session = Depends(get_db)):
    """Reset user PIN"""
    try:
        from sqlalchemy import text
        import hashlib
        
        # Hash the PIN
        pin_hash = hashlib.sha256(request.new_pin.encode()).hexdigest()
        
        db.execute(text("""
            UPDATE users SET pin_hash = :pin_hash, updated_at = :updated_at
            WHERE id = :user_id
        """), {
            "user_id": user_id,
            "pin_hash": pin_hash,
            "updated_at": datetime.utcnow()
        })
        
        db.commit()
        
        return {"success": True, "message": "PIN reset successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# DEVICE MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/devices", response_model=dict)
async def register_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """Register a new device"""
    try:
        from sqlalchemy import text
        
        device_id = str(uuid.uuid4())
        
        db.execute(text("""
            INSERT INTO devices (id, device_uuid, device_name, device_type, user_id, is_active, created_at)
            VALUES (:id, :device_uuid, :device_name, :device_type, :user_id, :is_active, :created_at)
        """), {
            "id": device_id,
            "device_uuid": device.device_uuid,
            "device_name": device.device_name,
            "device_type": device.device_type,
            "user_id": device.user_id,
            "is_active": True,
            "created_at": datetime.utcnow()
        })
        
        db.commit()
        
        return {
            "success": True,
            "data": {
                "id": device_id,
                "device_uuid": device.device_uuid,
                "device_name": device.device_name,
                "device_type": device.device_type,
                "user_id": device.user_id,
                "is_active": True,
                "last_seen": None,
                "created_at": datetime.utcnow()
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/devices", response_model=dict)
async def list_devices(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List registered devices"""
    try:
        from sqlalchemy import text
        
        where_clause = "1=1"
        params = {}
        
        if user_id:
            where_clause += " AND user_id = :user_id"
            params["user_id"] = user_id
        
        # Get total count
        result = db.execute(text(f"""
            SELECT COUNT(*) as total FROM devices WHERE {where_clause}
        """), params).fetchone()
        total = result[0] if result else 0
        
        # Get paginated results
        offset = (page - 1) * per_page
        results = db.execute(text(f"""
            SELECT id, device_uuid, device_name, device_type, user_id, is_active, last_seen, created_at
            FROM devices
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """), {**params, "limit": per_page, "offset": offset}).fetchall()
        
        devices = [
            {
                "id": row[0],
                "device_uuid": row[1],
                "device_name": row[2],
                "device_type": row[3],
                "user_id": row[4],
                "is_active": row[5],
                "last_seen": row[6],
                "created_at": row[7]
            }
            for row in results
        ]
        
        return {
            "success": True,
            "data": {
                "devices": devices,
                "total": total,
                "page": page,
                "per_page": per_page
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/devices/{device_id}", response_model=dict)
async def update_device(device_id: str, device: DeviceUpdate, db: Session = Depends(get_db)):
    """Update device details"""
    try:
        from sqlalchemy import text
        
        update_fields = []
        params = {"device_id": device_id}
        
        if device.device_name is not None:
            update_fields.append("device_name = :device_name")
            params["device_name"] = device.device_name
        if device.is_active is not None:
            update_fields.append("is_active = :is_active")
            params["is_active"] = device.is_active
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        db.execute(text(f"""
            UPDATE devices SET {', '.join(update_fields)} WHERE id = :device_id
        """), params)
        
        db.commit()
        
        return {"success": True, "message": "Device updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/devices/{device_id}")
async def deregister_device(device_id: str, db: Session = Depends(get_db)):
    """Deregister device"""
    try:
        from sqlalchemy import text
        
        db.execute(text("""
            UPDATE devices SET is_active = FALSE WHERE id = :device_id
        """), {"device_id": device_id})
        
        db.commit()
        
        return {"success": True, "message": "Device deregistered successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# GST CONFIGURATION ENDPOINTS
# ============================================================================

@router.get("/gst-rates", response_model=dict)
async def get_gst_rates(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all GST rates"""
    try:
        from sqlalchemy import text
        
        # Get total count
        result = db.execute(text("""
            SELECT COUNT(*) as total FROM gst_rates WHERE is_active = TRUE
        """)).fetchone()
        total = result[0] if result else 0
        
        # Get paginated results
        offset = (page - 1) * per_page
        results = db.execute(text("""
            SELECT id, category, rate, description, effective_date, created_at
            FROM gst_rates
            WHERE is_active = TRUE
            ORDER BY effective_date DESC
            LIMIT :limit OFFSET :offset
        """), {"limit": per_page, "offset": offset}).fetchall()
        
        rates = [
            {
                "id": row[0],
                "category": row[1],
                "rate": row[2],
                "description": row[3],
                "effective_date": row[4],
                "created_at": row[5],
                "is_active": True
            }
            for row in results
        ]
        
        return {
            "success": True,
            "data": {
                "gst_rates": rates,
                "total": total,
                "page": page,
                "per_page": per_page
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gst-rates", response_model=dict)
async def create_gst_rate(rate: GSTRateCreate, db: Session = Depends(get_db)):
    """Create a new GST rate"""
    try:
        from sqlalchemy import text
        
        rate_id = str(uuid.uuid4())
        
        db.execute(text("""
            INSERT INTO gst_rates (id, category, rate, description, effective_date, is_active, created_at)
            VALUES (:id, :category, :rate, :description, :effective_date, :is_active, :created_at)
        """), {
            "id": rate_id,
            "category": rate.category,
            "rate": rate.rate,
            "description": rate.description,
            "effective_date": rate.effective_date,
            "is_active": True,
            "created_at": datetime.utcnow()
        })
        
        db.commit()
        
        return {
            "success": True,
            "data": {
                "id": rate_id,
                "category": rate.category,
                "rate": rate.rate,
                "description": rate.description,
                "effective_date": rate.effective_date,
                "is_active": True,
                "created_at": datetime.utcnow()
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/gst-rates/{rate_id}", response_model=dict)
async def update_gst_rate(rate_id: str, rate: GSTRateUpdate, db: Session = Depends(get_db)):
    """Update GST rate"""
    try:
        from sqlalchemy import text
        
        update_fields = []
        params = {"rate_id": rate_id}
        
        if rate.rate is not None:
            update_fields.append("rate = :rate")
            params["rate"] = rate.rate
        if rate.description is not None:
            update_fields.append("description = :description")
            params["description"] = rate.description
        if rate.is_active is not None:
            update_fields.append("is_active = :is_active")
            params["is_active"] = rate.is_active
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        db.execute(text(f"""
            UPDATE gst_rates SET {', '.join(update_fields)} WHERE id = :rate_id
        """), params)
        
        db.commit()
        
        return {"success": True, "message": "GST rate updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/gst-rates/{rate_id}")
async def delete_gst_rate(rate_id: str, db: Session = Depends(get_db)):
    """Delete GST rate (soft delete)"""
    try:
        from sqlalchemy import text
        
        db.execute(text("""
            UPDATE gst_rates SET is_active = FALSE WHERE id = :rate_id
        """), {"rate_id": rate_id})
        
        db.commit()
        
        return {"success": True, "message": "GST rate deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
