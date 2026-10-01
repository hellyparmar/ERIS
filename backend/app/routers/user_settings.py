"""Authenticated profile and password settings."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.security import hash_password, verify_password
from app.database import get_db_sync_dependency
from app.models.users import User


router = APIRouter(prefix="/settings", tags=["settings"])


class UserProfile(BaseModel):
    name: str = Field(min_length=1, max_length=201)
    email: str
    phone: Optional[str] = Field(default=None, max_length=20)
    role: str


class UserProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=201)
    phone: Optional[str] = Field(default=None, max_length=20)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


def _serialize(user: User) -> UserProfile:
    role = user.role.name if hasattr(user.role, "name") else str(user.role)
    return UserProfile(name=user.full_name, email=user.email, phone=user.phone, role=role)


@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_active_user)) -> Any:
    return _serialize(current_user)


@router.put("/profile", response_model=UserProfile)
async def update_profile(
    profile: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_sync_dependency),
) -> Any:
    current_user.full_name = profile.name.strip()
    current_user.phone = profile.phone.strip() if profile.phone else None
    db.commit()
    db.refresh(current_user)
    return _serialize(current_user)


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_sync_dependency),
) -> Any:
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
    if request.current_password == request.new_password:
        raise HTTPException(status_code=400, detail="New password must differ from the current password")
    current_user.password_hash = hash_password(request.new_password)
    db.commit()
    return {"message": "Password changed successfully"}
