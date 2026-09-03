from datetime import datetime
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.database import get_db
from app.models.users import User, Role
from app.core.security import (
    verify_password,
    create_access_token,
    hash_password,
    verify_token,
    validate_password_strength,
    sanitize_input
)
from app.api.deps import get_current_active_user, require_role
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

router = APIRouter(prefix="/auth", tags=["auth"])

limiter = Limiter(key_func=get_remote_address)

async def _execute(db: Any, stmt: Any) -> Any:
    """Execute SQL statement handling both sync and async sessions."""
    from sqlalchemy.ext.asyncio import AsyncSession
    if isinstance(db, AsyncSession):
        return await db.execute(stmt)
    return db.execute(stmt)

async def _commit(db: Any) -> None:
    """Commit transaction handling both sync and async sessions."""
    from sqlalchemy.ext.asyncio import AsyncSession
    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

async def _refresh(db: Any, instance: Any) -> None:
    """Refresh model instance handling both sync and async sessions."""
    from sqlalchemy.ext.asyncio import AsyncSession
    if isinstance(db, AsyncSession):
        await db.refresh(instance)
    else:
        db.refresh(instance)

async def _rollback(db: Any) -> None:
    """Rollback transaction handling both sync and async sessions."""
    from sqlalchemy.ext.asyncio import AsyncSession
    if isinstance(db, AsyncSession):
        await db.rollback()
    else:
        db.rollback()

class RegisterRequest(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    role: str = "outlet_manager"

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    organization_id: Optional[int] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

@router.post("/login", response_model=LoginResponse)
@limiter.limit("1000/minute")
async def login(
    request: Request,
    oauth_request: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    result = await _execute(db,
        select(User).where(User.username == oauth_request.username, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(oauth_request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    role_name = "staff"
    role_result = await _execute(db, select(Role.name).where(Role.id == user.role_id))
    role_row = role_result.scalar_one_or_none()
    if role_row:
        role_name = role_row

    access_token = create_access_token({
        "sub": user.username,
        "user_id": str(user.id),
        "role": role_name
    })

    user_data = {
        "id": user.id,
        "username": user.username,
        "role": role_name,
        "organization_id": user.organization_id,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }
    

class LoginJsonRequest(BaseModel):
    username: str
    password: str

@router.post("/login/json", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login_json(
    request: Request,
    body: LoginJsonRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    result = await _execute(db,
        select(User).where(User.username == body.username, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    role_name = "staff"
    role_result = await _execute(db, select(Role.name).where(Role.id == user.role_id))
    role_row = role_result.scalar_one_or_none()
    if role_row:
        role_name = role_row

    access_token = create_access_token({
        "sub": user.username,
        "user_id": str(user.id),
        "role": role_name
    })

    user_data = {
        "id": user.id,
        "username": user.username,
        "role": role_name,
        "organization_id": user.organization_id,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/refresh", response_model=dict)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token.
    
    ERROR FIXES:
    - Uses await for all async database operations
    - Proper error handling
    """
    try:
        payload = verify_token(body.refresh_token)
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    try:
        result = await _execute(db, select(User).options(joinedload(User.role)).join(Role, User.role_id == Role.id).where(User.username == username))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        access_token = create_access_token({"sub": user.username, "role": user.role.name if user.role else 'staff'})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Logout user (client should discard tokens).
    
    Note: In production, implement token blacklisting with Redis
    """
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserOut)
async def read_users_me(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Any:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    
    try:
        payload = verify_token(token)
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except:
        raise credentials_exception
    
    result = await _execute(db, select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise credentials_exception

    role_name = "staff"
    role_result = await _execute(db, select(Role.name).where(Role.id == user.role_id))
    role_row = role_result.scalar_one_or_none()
    if role_row:
        role_name = role_row
    
    return {
        "id": user.id,
        "username": user.username,
        "role": role_name,
        "organization_id": user.organization_id,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }

@router.post("/register", response_model=dict)
@limiter.limit("3/minute")
async def register(
    request: Request,
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "area_manager"))
) -> Any:
    """
    Register a new user (only super_admin or area_manager can register).
    
    SECURITY FEATURES:
    - Password strength validation (min 12 chars, uppercase, lowercase, digit, special)
    - Input sanitization to prevent injection attacks
    - Uses async/await for all database operations
    - Proper transaction handling
    """
    try:
        # Sanitize inputs
        username = sanitize_input(req.username, "username", 50)
        first_name = sanitize_input(req.first_name, "first_name", 100)
        last_name = sanitize_input(req.last_name, "last_name", 100)
        
        # Validate password strength
        is_valid_password, error_msg = validate_password_strength(req.password)
        if not is_valid_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Check if user already exists
        result = await _execute(db, select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username already exists"
            )

        # Resolve role relationship
        req_role = req.role.lower().replace(' ', '_')
        if req_role == "staff":
            req_role = "outlet_manager"
        elif req_role in ("manager", "outlet_manager"):
            req_role = "outlet_manager"
        elif req_role in ("admin", "superadmin", "super_admin"):
            req_role = "super_admin"

        role_result = await _execute(db, select(Role).where(Role.name == req_role))
        role_obj = role_result.scalar_one_or_none()
        if not role_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role specified"
            )

        # Hash password
        hashed_password = hash_password(req.password)

        # Create user
        new_user = User(
            username=username,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role=role_obj,
            organization_id=current_user.organization_id,
            is_active=True,
            created_at=datetime.utcnow()
        )

        db.add(new_user)
        await _commit(db)
        await _refresh(db, new_user)

        from app.services.audit_service import log_audit_action
        await log_audit_action(
            db=db,
            action="register_user",
            performed_by=current_user.id,
            context={"new_user_id": new_user.id, "username": username, "role": req_role}
        )

        logger.info(f"New user registered: {username}")

        return {
            "message": "User created successfully",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "full_name": new_user.full_name,
                "role": req_role
            }
        }
    except HTTPException:
        raise
    except ValueError as e:
        await _rollback(db)
        logger.warning(f"Input validation error during registration: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await _rollback(db)
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")
