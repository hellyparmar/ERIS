"""Authentication (JWT access + refresh tokens, bcrypt) and authorization helpers.

Roles: admin (everything), manager (operations for assigned outlets), staff (billing & stock lookup at assigned
outlets), viewer (read-only dashboards, forecasts, analytics and AI questions). Outlet access is enforced here at the
application level - every query is narrowed with `scoped_outlet_ids`.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)
NO_OUTLETS = [-1]  # matches nothing: a non-admin user with no assigned outlet sees no data


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=10)).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def _encode(payload: dict, lifetime: timedelta) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({**payload, "iat": now, "exp": now + lifetime}, settings.JWT_SECRET_KEY,
                      algorithm=settings.JWT_ALGORITHM)


def create_access_token(user: User) -> str:
    return _encode({"sub": str(user.id), "role": user.role, "typ": "access"},
                   timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(user: User) -> str:
    return _encode({"sub": str(user.id), "typ": "refresh", "ver": user.token_version or 0},
                   timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))


def token_pair(user: User) -> dict:
    return {"access_token": create_access_token(user), "refresh_token": create_refresh_token(user),
            "token_type": "bearer", "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60}


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired", headers={"WWW-Authenticate": "Bearer"}) from None
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token", headers={"WWW-Authenticate": "Bearer"}) from None
    if payload.get("typ", "access") != expected_type:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")
    return payload


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "Not authenticated", headers={"WWW-Authenticate": "Bearer"}
    )
    if creds is None:
        raise unauthorized
    payload = decode_token(creds.credentials, "access")
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise unauthorized from None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    db.info["user_id"] = user.id  # attributes audited changes in this request's session to this user
    return user


def require_roles(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission for this action")
        return user

    return checker


require_admin = require_roles("admin")
require_manager = require_roles("admin", "manager")
require_writer = require_roles("admin", "manager", "staff")  # anyone except read-only viewers


def scoped_outlet_ids(user: User, requested: int | None = None) -> list[int] | None:
    """Outlets the user may see, narrowed by an optional requested outlet.

    Returns None for "all outlets" (admins without a filter).
    """
    if user.role == "admin":
        return [requested] if requested else None
    allowed = user.outlet_ids
    if requested:
        if requested not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You don't have access to that outlet")
        return [requested]
    return allowed or NO_OUTLETS


def ensure_outlet_access(user: User, outlet_id: int) -> None:
    if user.role != "admin" and outlet_id not in user.outlet_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You don't have access to that outlet")
