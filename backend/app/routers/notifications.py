from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.core.security import get_current_user
from app.models.notification import Notification, NotificationTypeEnum
from app.models.users import User
router = APIRouter(prefix="/notifications", tags=["Notifications"])

# Pydantic models for response
class NotificationResponse(BaseModel):
    id: int
    user_id: int
    outlet_id: Optional[int]
    type: NotificationTypeEnum
    title: str
    message: str
    is_read: bool
    created_at: datetime
    link: Optional[str]

    class Config:
        from_attributes = True

class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    unread_count: int
    total: int
    page: int
    limit: int

@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 20
    
    offset = (page - 1) * limit

    # Query notifications
    query = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    notifications = result.scalars().all()

    # Get total count
    total_query = select(func.count(Notification.id)).where(Notification.user_id == current_user.id)
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    # Get unread count
    unread_query = select(func.count(Notification.id)).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    )
    unread_result = await db.execute(unread_query)
    unread_count = unread_result.scalar() or 0

    return {
        "items": notifications,
        "unread_count": unread_count,
        "total": total,
        "page": page,
        "limit": limit
    }

@router.put("/mark-all-read")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id)
        .values(is_read=True)
    )
    await db.commit()
    return {"status": "success", "message": "All notifications marked as read"}

@router.put("/{id}/read")
async def mark_notification_as_read(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Notification).where(
        Notification.id == id,
        Notification.user_id == current_user.id
    )
    result = await db.execute(query)
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    notification.is_read = True
    await db.commit()
    return {"status": "success", "message": "Notification marked as read"}

@router.post("/test-ai")
async def test_ai_endpoint(prompt: str = "Hello, what can you do?", current_user: User = Depends(get_current_user)):
    """Test the AI provider connectivity"""
    from app.config import settings
    from app.ml.assistant.llm_provider import llm

    if not settings.ENABLE_AI_ASSISTANT:
        raise HTTPException(status_code=400, detail="AI Assistant is disabled in config")

    response = await llm.chat([{"role": "user", "content": prompt}])
    return {"status": "success", "provider": llm.provider, "response": response}
