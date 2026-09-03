from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLogEntry
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def log_audit_action(
    db: AsyncSession,
    action: str,
    performed_by: int,
    context: Optional[Dict[str, Any]] = None,
    approved_by: Optional[int] = None
) -> None:
    """
    Write an audit log entry for a sensitive action.
    """
    try:
        audit_entry = AuditLogEntry(
            action=action,
            performed_by=performed_by,
            context=context or {},
            approved_by=approved_by
        )
        db.add(audit_entry)
        # Flush to ensure the audit log is part of the current transaction
        await db.flush()
    except Exception as e:
        logger.error(f"Failed to write audit log for action {action}: {e}")
        # Log the error but don't fail the transaction

from sqlalchemy.orm import Session

def log_audit_action_sync(
    db: Session,
    action: str,
    performed_by: int,
    context: Optional[Dict[str, Any]] = None,
    approved_by: Optional[int] = None
) -> None:
    """
    Write an audit log entry for a sensitive action synchronously.
    """
    try:
        audit_entry = AuditLogEntry(
            action=action,
            performed_by=performed_by,
            context=context or {},
            approved_by=approved_by
        )
        db.add(audit_entry)
        db.flush()
    except Exception as e:
        logger.error(f"Failed to write sync audit log for action {action}: {e}")
