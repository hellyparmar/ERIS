from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, Outlet
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

    result = await db.execute(select(User).where(User.email == email))
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
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

def get_outlet_scope(current_user: User, db: Session) -> List[int]:
    if current_user.role == "super_admin":
        outlets = db.query(Outlet).all()
        return [o.id for o in outlets]
    elif current_user.role in ["outlet_manager", "staff"]:
        return [current_user.outlet_id] if current_user.outlet_id else []
    elif current_user.role == "area_manager":
        # Assume area_manager can access outlets in the same city as their outlet
        if current_user.outlet_id:
            outlet = db.query(Outlet).filter(Outlet.id == current_user.outlet_id).first()
            if outlet:
                outlets = db.query(Outlet).filter(Outlet.city == outlet.city).all()
                return [o.id for o in outlets]
        return []
    return []