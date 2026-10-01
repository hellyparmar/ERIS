import threading
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Outlet, User
from app.routers.common import get_or_404
from app.schemas import ChangePasswordIn, LoginIn, ProfileIn, UserIn, UserUpdate
from app.security import create_access_token, get_current_user, hash_password, require_admin, verify_password

router = APIRouter(prefix="/api", tags=["auth & users"])


def user_dict(u: User) -> dict:
    return {
        "id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role, "outlet_id": u.outlet_id,
        "outlet_name": u.outlet.name if u.outlet else None, "is_active": u.is_active,
        "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


# Brute-force protection: 5 failed attempts per email + client within 15 minutes locks that pair out.
MAX_FAILURES, WINDOW_SECONDS = 5, 15 * 60
_failures: dict[tuple[str, str], list[float]] = {}
_failures_lock = threading.Lock()


def _recent_failures(key: tuple[str, str]) -> list[float]:
    now = time.time()
    with _failures_lock:
        hits = [t for t in _failures.get(key, []) if now - t < WINDOW_SECONDS]
        _failures[key] = hits
        return hits


@router.post("/auth/login")
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    key = (email, request.client.host if request.client else "?")
    hits = _recent_failures(key)
    if len(hits) >= MAX_FAILURES:
        wait = int(WINDOW_SECONDS - (time.time() - hits[0])) // 60 + 1
        raise HTTPException(429, f"Too many failed sign-in attempts. Try again in {wait} minute(s).")
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    if user is None or not verify_password(body.password, user.password_hash):
        with _failures_lock:
            _failures.setdefault(key, []).append(time.time())
        raise HTTPException(401, "Incorrect email or password")
    with _failures_lock:
        _failures.pop(key, None)
    if not user.is_active:
        raise HTTPException(403, "This account has been deactivated")
    user.last_login_at = datetime.now()
    db.commit()
    return {"access_token": create_access_token(user), "token_type": "bearer", "user": user_dict(user)}


@router.get("/auth/me")
def me(user: User = Depends(get_current_user)):
    return user_dict(user)


@router.patch("/auth/me")
def update_me(body: ProfileIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.full_name = body.full_name.strip()
    db.commit()
    return user_dict(user)


@router.post("/auth/change-password")
def change_password(body: ChangePasswordIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------------------------------ users (admin)
@router.get("/users")
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return [user_dict(u) for u in db.scalars(select(User).order_by(User.role, User.full_name)).all()]


def _validate_outlet(db: Session, role: str, outlet_id: int | None) -> None:
    if role in ("manager", "staff") and not outlet_id:
        raise HTTPException(400, "Managers and staff must be assigned to an outlet")
    if outlet_id:
        get_or_404(db, Outlet, outlet_id, "Outlet")


@router.post("/users", status_code=201)
def create_user(body: UserIn, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.scalar(select(User.id).where(func.lower(User.email) == body.email.lower())):
        raise HTTPException(409, "A user with this email already exists")
    _validate_outlet(db, body.role, body.outlet_id)
    user = User(email=body.email.lower(), full_name=body.full_name.strip(), role=body.role,
                outlet_id=body.outlet_id if body.role != "admin" else None,
                password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_dict(user)


@router.patch("/users/{user_id}")
def update_user(user_id: int, body: UserUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = get_or_404(db, User, user_id, "User")
    data = body.model_dump(exclude_unset=True)
    if user.id == admin.id and (data.get("role", "admin") != "admin" or data.get("is_active") is False):
        raise HTTPException(400, "You cannot demote or deactivate your own account")
    role = data.get("role", user.role)
    outlet_id = data.get("outlet_id", user.outlet_id)
    _validate_outlet(db, role, outlet_id)
    if "password" in data:
        user.password_hash = hash_password(data.pop("password"))
    for k, v in data.items():
        setattr(user, k, v)
    if user.role == "admin":
        user.outlet_id = None
    db.commit()
    db.refresh(user)
    return user_dict(user)


@router.delete("/users/{user_id}")
def deactivate_user(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = get_or_404(db, User, user_id, "User")
    if user.id == admin.id:
        raise HTTPException(400, "You cannot deactivate your own account")
    user.is_active = False
    db.commit()
    return {"ok": True}
