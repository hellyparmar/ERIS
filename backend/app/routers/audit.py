from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional, List, Dict, Any
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
    current_user: User = Depends(require_role("super_admin", "area_manager"))
):
    """
    Retrieve audit logs. Only accessible by super_admin or area_manager.
    """
    try:
        stmt = select(AuditLogEntry)
        
        if action:
            stmt = stmt.where(AuditLogEntry.action == action)
        if performed_by:
            stmt = stmt.where(AuditLogEntry.performed_by == performed_by)
        if start_date:
            stmt = stmt.where(AuditLogEntry.timestamp >= start_date)
        if end_date:
            stmt = stmt.where(AuditLogEntry.timestamp <= end_date)
            
        stmt = stmt.order_by(desc(AuditLogEntry.timestamp))
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
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "context": log.context
                }
                for log in logs
            ],
            "page": page,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audit logs: {e}")
