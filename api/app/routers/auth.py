import logging
import threading
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app import clock
from app.db import get_db
from app.models import Outlet, User
from app.routers.common import get_or_404
from app.schemas import ChangePasswordIn, LoginIn, ProfileIn, RefreshIn, UserIn, UserUpdate
from app.security import decode_token, get_current_user, hash_password, require_admin, token_pair, verify_password
from app.services.audit import audit

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["auth & users"])


def user_dict(u: User) -> dict:
    return {
        "id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role,
        "outlet_ids": u.outlet_ids, "outlet_names": [o.name for o in u.outlets],
        "is_active": u.is_active,
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
    try:
        user.last_login_at = clock.now()
        db.commit()
    except OperationalError:  # e.g. SQLite busy while demo data is being generated - not a reason to refuse sign-in
        db.rollback()
        log.warning("could not record last login for %s", user.email)
    return {**token_pair(user), "user": user_dict(user)}


@router.post("/auth/refresh")
def refresh(body: RefreshIn, db: Session = Depends(get_db)):
    """Exchange a refresh token for a new access + refresh token pair (rotation)."""
    payload = decode_token(body.refresh_token, "refresh")
    user = db.get(User, int(payload.get("sub", 0)))
    if user is None or not user.is_active or payload.get("ver") != (user.token_version or 0):
        raise HTTPException(401, "Session is no longer valid - please sign in again")
    return {**token_pair(user), "user": user_dict(user)}


@router.post("/auth/logout-all")
def logout_everywhere(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Invalidate every refresh token of this user (all devices)."""
    user.token_version = (user.token_version or 0) + 1
    db.commit()
    return {"ok": True}


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
    user.token_version = (user.token_version or 0) + 1  # sign out other sessions
    audit(db, user, "user.password", "user", user.id, "Changed own password")
    db.commit()
    return {**token_pair(user), "ok": True}


# ------------------------------------------------------------------------------------------ users (admin)
@router.get("/users")
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return [user_dict(u) for u in db.scalars(select(User).order_by(User.role, User.full_name)).all()]


def _outlets_for(db: Session, role: str, outlet_ids: list[int] | None) -> list[Outlet]:
    if role == "admin":
        return []
    if not outlet_ids:
        raise HTTPException(400, "Assign at least one outlet to managers, staff and viewers")
    outlets = db.scalars(select(Outlet).where(Outlet.id.in_(outlet_ids))).all()
    if len(outlets) != len(set(outlet_ids)):
        raise HTTPException(404, "Outlet not found")
    return list(outlets)


@router.post("/users", status_code=201)
def create_user(body: UserIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.scalar(select(User.id).where(func.lower(User.email) == body.email.lower())):
        raise HTTPException(409, "A user with this email already exists")
    user = User(email=body.email.lower(), full_name=body.full_name.strip(), role=body.role,
                password_hash=hash_password(body.password), outlets=_outlets_for(db, body.role, body.outlet_ids))
    db.add(user)
    db.flush()
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
    outlet_ids = data.pop("outlet_ids", None)
    user.outlets = _outlets_for(db, role, outlet_ids if outlet_ids is not None else user.outlet_ids)
    if "password" in data:
        user.password_hash = hash_password(data.pop("password"))
        user.token_version = (user.token_version or 0) + 1
    if data.get("is_active") is False or data.get("role", user.role) != user.role:
        user.token_version = (user.token_version or 0) + 1
    for k, v in data.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user_dict(user)


@router.delete("/users/{user_id}")
def deactivate_user(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = get_or_404(db, User, user_id, "User")
    if user.id == admin.id:
        raise HTTPException(400, "You cannot deactivate your own account")
    user.is_active = False
    user.token_version = (user.token_version or 0) + 1
    db.commit()
    return {"ok": True}
