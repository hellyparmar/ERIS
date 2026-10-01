from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.users import User
from app.models.audit import AuditLogEntry
from app.api.deps import require_role

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/")
async def get_audit_logs(
    action: Optional[str] = None,
    performed_by: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """
    Retrieve audit logs. Only accessible by admins or managers.
    """
    try:
        stmt = (
            select(AuditLogEntry)
            .join(User, User.id == AuditLogEntry.performed_by)
            .where(User.organization_id == current_user.organization_id)
        )

        if action:
            stmt = stmt.where(AuditLogEntry.action == action)
        if performed_by:
            stmt = stmt.where(AuditLogEntry.performed_by == performed_by)
        if start_date:
            stmt = stmt.where(AuditLogEntry.created_at >= start_date)
        if end_date:
            stmt = stmt.where(AuditLogEntry.created_at <= end_date)

        stmt = stmt.order_by(desc(AuditLogEntry.created_at))
        stmt = stmt.offset((page - 1) * limit).limit(limit)

        result = await db.execute(stmt)
        logs = result.scalars().all()

        return {
            "success": True,
            "data": [
                {
                    "id": log.id,
                    "action": log.action,
                    "performed_by": log.performed_by,
                    "approved_by": log.approved_by,
                    "timestamp": log.created_at.isoformat() if log.created_at else None,
                    "context": log.context,
                }
                for log in logs
            ],
            "page": page,
            "limit": limit,
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch audit logs")
