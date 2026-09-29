from typing import List, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import User, Outlet, UserOutletAccess
from app.core.security import decode_token
from app.core.roles import ADMIN, normalize_role, user_role

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def _execute_db(db: Any, stmt: Any) -> Any:
    """Execute SQL statement supporting both AsyncSession and sync Session."""
    if isinstance(db, AsyncSession):
        return await db.execute(stmt)
    return db.execute(stmt)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Any = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    result = await _execute_db(
        db,
        select(User)
        .options(selectinload(User.role), selectinload(User.outlet_access))
        .where(User.username == username)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(*roles):
    allowed_roles = {normalize_role(role) for role in roles}

    def role_checker(current_user: User = Depends(get_current_active_user)):
        if user_role(current_user) not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

async def get_accessible_outlet_ids(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[int]:
    """
    Dependency that returns the list of outlet IDs the current user is allowed to access.
    - admin: Returns all outlet IDs in the system.
    - manager / viewer: Returns IDs assigned through user_outlet_access.
    """
    role_name = user_role(current_user)
    
    if role_name == ADMIN:
        result = await _execute_db(db, select(Outlet.id))
        return [row[0] for row in result.fetchall()]
        
    else:
        if hasattr(current_user, 'outlet_access') and current_user.outlet_access:
            return [access.outlet_id for access in current_user.outlet_access]
        if getattr(current_user, 'outlet_id', None):
            return [current_user.outlet_id]
        result = await _execute_db(
            db,
            select(UserOutletAccess.outlet_id).where(UserOutletAccess.user_id == current_user.id)
        )
        rows = [row[0] for row in result.fetchall()]
        return rows if rows else []

def get_outlet_scope(current_user: User, db: Session) -> List[int]:
    """
    Synchronous helper that returns the list of outlet IDs the current user is allowed to access.
    """
    role_name = user_role(current_user)
    
    if role_name == ADMIN:
        outlets = db.query(Outlet).all()
        return [o.id for o in outlets]
    else:
        access_records = db.query(UserOutletAccess).filter(UserOutletAccess.user_id == current_user.id).all()
        if access_records:
            return [access.outlet_id for access in access_records]
        if getattr(current_user, 'outlet_id', None):
            return [current_user.outlet_id]
        return []
