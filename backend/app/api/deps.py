from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import User, Outlet, UserOutletAccess
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except:
        raise credentials_exception

    result = await db.execute(
        select(User)
        .options(selectinload(User.role), selectinload(User.outlet_access))
        .where(User.email == email)
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
    def role_checker(current_user: User = Depends(get_current_active_user)):
        role_name = current_user.role.name if current_user.role else ""
        if role_name not in roles:
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
    - super_admin: Returns all outlet IDs in the system.
    - area_manager: Returns IDs of all outlets assigned to them in user_outlet_access.
    - outlet_manager: Returns ID of the single assigned outlet.
    """
    role_name = current_user.role.name if current_user.role else ""
    
    if role_name == "super_admin":
        result = await db.execute(select(Outlet.id))
        return [row[0] for row in result.fetchall()]
        
    elif role_name == "area_manager":
        if hasattr(current_user, 'outlet_access') and current_user.outlet_access:
            return [access.outlet_id for access in current_user.outlet_access]
        result = await db.execute(
            select(UserOutletAccess.outlet_id).where(UserOutletAccess.user_id == current_user.id)
        )
        return [row[0] for row in result.fetchall()]
        
    elif role_name == "outlet_manager":
        if current_user.outlet_id:
            return [current_user.outlet_id]
        if hasattr(current_user, 'outlet_access') and current_user.outlet_access:
            return [access.outlet_id for access in current_user.outlet_access]
        result = await db.execute(
            select(UserOutletAccess.outlet_id).where(UserOutletAccess.user_id == current_user.id).limit(1)
        )
        row = result.fetchone()
        if row:
            return [row[0]]
        return []
        
    return []

def get_outlet_scope(current_user: User, db: Session) -> List[int]:
    role_name = current_user.role.name if current_user.role else ""
    
    if role_name == "super_admin":
        outlets = db.query(Outlet).all()
        return [o.id for o in outlets]
    elif role_name == "area_manager":
        access_records = db.query(UserOutletAccess).filter(UserOutletAccess.user_id == current_user.id).all()
        return [access.outlet_id for access in access_records]
    elif role_name == "outlet_manager":
        access_records = db.query(UserOutletAccess).filter(UserOutletAccess.user_id == current_user.id).all()
        if access_records:
            return [access_records[0].outlet_id]
        if current_user.outlet_id:
            return [current_user.outlet_id]
        return []
    return []