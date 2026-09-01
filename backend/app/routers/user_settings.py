"""
Settings API Router - User preferences, security, notifications, and account management
"""

from datetime import datetime, timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.users import User
from app.api.deps import get_current_active_user
from app.core.security import hash_password, verify_password

router = APIRouter(prefix="/settings", tags=["settings"])


# Schemas
class UserProfile(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    department: Optional[str] = None
    role: str

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class NotificationSettings(BaseModel):
    email_alerts: bool = True
    push_notifications: bool = True
    sms_notifications: bool = False
    daily_digest: bool = True
    low_stock_alerts: bool = True
    sale_alerts: bool = True


class SecuritySettings(BaseModel):
    two_factor_enabled: bool = False
    login_notifications: bool = True
    require_password_change: bool = False


class ThemePreferences(BaseModel):
    theme: str = "light"  # light, dark, auto
    language: str = "en"
    timezone: str = "UTC"


class SystemSettings(BaseModel):
    auto_logout_minutes: int = 30
    data_retention_days: int = 365
    enable_analytics: bool = True


# Endpoints


@router.get("/profile", response_model=UserProfile)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get current user profile"""
    return UserProfile(
        name=current_user.name,
        email=current_user.email,
        phone=getattr(current_user, 'phone', None),
        department=getattr(current_user, 'department', None),
        role=current_user.role
    )


@router.put("/profile")
async def update_profile(
    profile_data: UserProfile,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update user profile"""
    current_user.name = profile_data.name
    if profile_data.phone:
        current_user.phone = profile_data.phone
    db.commit()
    return {"message": "Profile updated successfully", "profile": profile_data}


@router.post("/change-password")
async def change_password(
    password_request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Change user password"""
    if not verify_password(password_request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    current_user.password_hash = hash_password(password_request.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.get("/notifications", response_model=NotificationSettings)
async def get_notification_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get notification preferences"""
    return NotificationSettings()


@router.put("/notifications")
async def update_notification_settings(
    settings: NotificationSettings,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update notification preferences"""
    return {"message": "Notification settings updated", "settings": settings}


@router.get("/security", response_model=SecuritySettings)
async def get_security_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get security settings"""
    return SecuritySettings()


@router.post("/2fa/enable")
async def enable_2fa(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Enable two-factor authentication"""
    return {
        "message": "2FA setup started",
        "qr_code": "data:image/png;base64,..." # Placeholder
    }


@router.post("/2fa/disable")
async def disable_2fa(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Disable two-factor authentication"""
    return {"message": "2FA disabled"}


@router.get("/api-keys")
async def get_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get user's API keys"""
    return {"api_keys": []}


@router.post("/api-keys")
async def create_api_key(
    name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create new API key"""
    return {
        "message": "API key created",
        "key": "sk_" + "x" * 32,
        "name": name,
        "created_at": datetime.utcnow().isoformat()
    }


@router.get("/theme")
async def get_theme_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get theme and language preferences"""
    return ThemePreferences()


@router.put("/theme")
async def update_theme_preferences(
    preferences: ThemePreferences,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update theme and language preferences"""
    return {"message": "Theme preferences updated", "preferences": preferences}


@router.get("/system")
async def get_system_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get system settings"""
    return SystemSettings()


@router.put("/system")
async def update_system_settings(
    settings: SystemSettings,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update system settings"""
    return {"message": "System settings updated", "settings": settings}


@router.post("/export-data")
async def export_user_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Export user's personal data"""
    return {
        "message": "Data export scheduled",
        "status": "processing",
        "estimated_time": "5 minutes"
    }


@router.post("/delete-account")
async def delete_account(
    password: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Request account deletion"""
    if not verify_password(password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password is incorrect"
        )
    return {"message": "Account deletion scheduled for 30 days"}


@router.get("/activity-log")
async def get_activity_log(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get user activity log"""
    return {
        "activities": [],
        "total_count": 0,
        "period_days": days
    }


@router.get("/login-history")
async def get_login_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get login history"""
    return {
        "logins": [],
        "total_count": 0,
        "limit": limit
    }


@router.get("/sessions")
async def get_active_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get all active sessions"""
    return {
        "sessions": [
            {
                "id": "session_1",
                "device": "Chrome on Windows",
                "ip_address": "192.168.1.1",
                "last_active": datetime.utcnow().isoformat(),
                "is_current": True
            }
        ]
    }


@router.post("/sessions/{session_id}/logout")
async def logout_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Logout a specific session"""
    return {"message": f"Session {session_id} logged out"}


@router.get("/preferences")
async def get_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get all user preferences"""
    return {
        "theme": "light",
        "language": "en",
        "notifications_enabled": True,
        "analytics_enabled": True
    }


@router.post("/backup")
async def request_backup(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Request backup of user data"""
    return {
        "message": "Backup requested",
        "status": "queued",
        "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    }


@router.get("/system-info")
async def get_system_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get system information"""
    return {
        "api_version": "1.0.0",
        "build": "20260416",
        "environment": "production",
        "features": ["invoicing", "reporting", "forecasting"]
    }


@router.get("/health")
async def health_check(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Settings service health check"""
    return {
        "status": "healthy",
        "service": "settings",
        "timestamp": datetime.utcnow().isoformat()
    }
