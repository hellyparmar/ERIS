"""
Audit Logging Utility
Helper functions for tracking sensitive database actions
"""

from sqlalchemy.orm import Session
from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, Optional

from app.api.db.audit_models import AuditLog
from app.models.multitenant_models import User

logger = logging.getLogger(__name__)

def log_audit_action(
    db: Session,
    action: str,
    table_name: str,
    record_id: str,
    user_id: Optional[int] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """
    Logs an action to the AuditLog table
    """
    try:
        audit_entry = AuditLog(
            action=action,
            table_name=table_name,
            record_id=str(record_id),
            user_id=user_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(audit_entry)
        db.commit()
    except Exception as e:
        # We don't want audit logging failures to break the main transaction, 
        # so we rollback the audit insert and just log an error
        logger.error(f"Failed to write audit log for {action} on {table_name}: {e}")
        db.rollback()
