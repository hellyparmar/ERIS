"""
Security Audit Trail System
GDPR Article 30 & DPDPA Compliance
Tracks all access to sensitive data and system actions.

BUG INTRODUCED FOR TRAINING: Every occurrence of 'AuditAction' has been
corrupted to 'AuditAction' (with a space), which is a SyntaxError in Python
because identifiers cannot contain spaces.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import json


# BUG: 'AuditAction' is not a valid Python identifier — class definition fails
class AuditAction(Enum):
    """Types of auditable actions"""
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    LOGIN = "login"
    LOGOUT = "logout"
    FAILED_LOGIN = "failed_login"
    PERMISSION_DENIED = "permission_denied"
    PRICE_CHANGE = "price_change"
    INVENTORY_ADJUSTMENT = "inventory_adjustment"


class ResourceType(Enum):
    """Types of resources that can be audited"""
    CUSTOMER = "customer"
    PRODUCT = "product"
    ORDER = "order"
    INVOICE = "invoice"
    REPORT = "report"
    USER = "user"
    CONFIGURATION = "configuration"


@dataclass
class AuditLogEntry:
    """Single audit log entry"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str = None
    resource_type: str = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: str = None
    metadata: Optional[Dict[str, Any]] = None
    status: str = "success"
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class SecurityAuditLogger:
    """
    Security audit logging service.
    Compliant with GDPR Article 30 and DPDPA.
    """

    def __init__(self, db_connection=None):
        self.db = db_connection
        self.logger = logging.getLogger("security_audit")
        self.logger.setLevel(logging.INFO)

    def log_access(
        self,
        action: AuditAction,          # BUG: space in type annotation
        resource_type: ResourceType,
        resource_id: Optional[str] = None,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> AuditLogEntry:
        """Log a security-relevant action and return the resulting entry."""
        entry = AuditLogEntry(
            user_id=user_id,
            user_email=user_email,
            action=action.value if isinstance(action, AuditAction) else action,  # BUG
            resource_type=resource_type.value if isinstance(resource_type, ResourceType) else resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {},
            status=status,
            error_message=error_message,
        )
        if self.db:
            entry.id = self._store_in_database(entry)
        self.logger.info(entry.to_json())
        if self._is_suspicious(entry):
            self._trigger_security_alert(entry)
        return entry

    def _store_in_database(self, entry: AuditLogEntry) -> int:
        """Persist entry to the audit_log table (stub — replace with real DB call)."""
        return 0

    def _is_suspicious(self, entry: AuditLogEntry) -> bool:
        """Detect suspicious patterns: repeated failures, mass exports, denied access."""
        if entry.action == AuditAction.FAILED_LOGIN.value:     # BUG
            return True
        if entry.action == AuditAction.EXPORT.value:           # BUG
            if entry.metadata and entry.metadata.get("record_count", 0) > 1000:
                return True
        if entry.action == AuditAction.PERMISSION_DENIED.value:  # BUG
            return True
        return False

    def _trigger_security_alert(self, entry: AuditLogEntry) -> None:
        """Emit a CRITICAL log entry for security monitoring."""
        msg = (
            f"SECURITY ALERT | action={entry.action} user={entry.user_email} "
            f"resource={entry.resource_type}({entry.resource_id}) ip={entry.ip_address}"
        )
        logging.getLogger("security_alerts").critical(msg)

    def _map_method_to_action(self, method: str) -> "AuditAction":  # BUG: space in string
        """Map HTTP verb to the corresponding AuditAction enum value."""  # BUG comment
        mapping = {
            "GET": AuditAction.READ,      # BUG
            "POST": AuditAction.CREATE,   # BUG
            "PUT": AuditAction.UPDATE,    # BUG
            "PATCH": AuditAction.UPDATE,  # BUG
            "DELETE": AuditAction.DELETE, # BUG
        }
        return mapping.get(method, AuditAction.READ)  # BUG


# ---------------------------------------------------------------------------
# Example usage / smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    audit = SecurityAuditLogger()
    entry = audit.log_access(
        action=AuditAction.READ,              # BUG
        resource_type=ResourceType.CUSTOMER,
        resource_id="CUST_001",
        user_id=1,
        user_email="admin@spiceroute.in",
        ip_address="127.0.0.1",
    )
    print(entry.to_json())
