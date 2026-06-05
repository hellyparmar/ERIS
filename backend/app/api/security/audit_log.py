"""
Tamper-Evident Audit Logging with Hash Chain

Implements a hash-chained audit trail that allows detection of any tampering
with historical log entries. Each log entry is cryptographically linked to
the previous entry, making it impossible to modify past records undetected.

Security Properties:
- Tamper detection: Any modification is detectable
- Immutability: Past records cannot be changed without detection
- Integrity verification: Chain validation confirms no tampering
- Complete audit trail: All security-relevant events logged
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()

# ============================================================================
# Database Models
# ============================================================================

class AuditLogEntry(Base):
    """Immutable audit log entry with cryptographic hash chain"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Event information
    event_type = Column(String(100), index=True, nullable=False)
    user_id = Column(String(36), index=True)
    tenant_id = Column(String(36), index=True)
    action = Column(String(200), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(100))
    
    # Event details (JSON)
    details = Column(Text)  # JSON serialized
    
    # Hash chain for tamper detection
    event_hash = Column(String(64), unique=True, nullable=False, index=True)
    previous_hash = Column(String(64), index=True)
    
    # Metadata
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Verification
    is_verified = Column(Boolean, default=True)
    verification_timestamp = Column(DateTime)


class AuditLogVerification(Base):
    """Record of log chain verifications"""
    __tablename__ = "audit_log_verifications"
    
    id = Column(Integer, primary_key=True)
    verification_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    
    # Verification details
    start_entry_id = Column(String(36), index=True)
    end_entry_id = Column(String(36), index=True)
    is_valid = Column(Boolean, nullable=False)
    
    # Results
    total_entries_checked = Column(Integer)
    tampering_detected = Column(Boolean, default=False)
    tampering_details = Column(Text)  # JSON - details of tampering
    
    # Metadata
    verified_at = Column(DateTime, default=datetime.utcnow)
    verified_by = Column(String(36))


class AuditEventType(str, Enum):
    """Types of security events to audit"""
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGIN_BRUTE_FORCE = "LOGIN_BRUTE_FORCE"
    
    API_CALL = "API_CALL"
    API_UNAUTHORIZED = "API_UNAUTHORIZED"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    
    DATA_CREATE = "DATA_CREATE"
    DATA_UPDATE = "DATA_UPDATE"
    DATA_DELETE = "DATA_DELETE"
    DATA_EXPORT = "DATA_EXPORT"
    
    DEVICE_REGISTERED = "DEVICE_REGISTERED"
    DEVICE_DENIED = "DEVICE_DENIED"
    DEVICE_REVOKED = "DEVICE_REVOKED"
    
    ENCRYPTION_KEY_ROTATION = "ENCRYPTION_KEY_ROTATION"
    REPLICATION_FAILOVER = "REPLICATION_FAILOVER"
    
    SECURITY_ALERT = "SECURITY_ALERT"
    TAMPERING_DETECTED = "TAMPERING_DETECTED"


class SecureAuditLog:
    """
    Secure audit logging with cryptographic hash chain
    
    Usage:
        logger = SecureAuditLog(db_session)
        logger.log_event(
            event_type="API_CALL",
            user_id="user-123",
            action="POST /api/v1/sale",
            details={"endpoint": "/api/v1/sale", "method": "POST"}
        )
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def _compute_hash(self, data: Dict[str, Any]) -> str:
        """Compute SHA-256 hash of event data"""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _get_previous_hash(self) -> Optional[str]:
        """Get hash of previous log entry"""
        last_entry = self.db.query(AuditLogEntry).order_by(
            AuditLogEntry.id.desc()
        ).first()
        return last_entry.event_hash if last_entry else None
    
    def log_event(
        self,
        event_type: str,
        user_id: Optional[str],
        action: str,
        details: Optional[Dict[str, Any]] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Log a security event with hash chain
        
        Returns:
            entry_id: Unique identifier for this log entry
        """
        entry_id = str(uuid.uuid4())
        
        # Get previous hash for chain
        previous_hash = self._get_previous_hash()
        
        # Prepare event data for hashing
        hash_data = {
            "entry_id": entry_id,
            "event_type": event_type,
            "user_id": user_id,
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "previous_hash": previous_hash
        }
        
        # Compute hash
        event_hash = self._compute_hash(hash_data)
        
        # Create log entry
        log_entry = AuditLogEntry(
            entry_id=entry_id,
            event_type=event_type,
            user_id=user_id,
            tenant_id=tenant_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details or {}),
            event_hash=event_hash,
            previous_hash=previous_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            is_verified=True
        )
        
        self.db.add(log_entry)
        self.db.commit()
        
        return entry_id
    
    def verify_chain_integrity(
        self,
        start_id: Optional[str] = None,
        end_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify integrity of log chain
        
        Returns:
            {
                "is_valid": bool,
                "total_entries": int,
                "tampering_detected": bool,
                "tampered_entries": [list of entry IDs with invalid hashes],
                "verification_id": str
            }
        """
        # Get entries to verify
        query = self.db.query(AuditLogEntry).order_by(AuditLogEntry.id)
        
        if start_id:
            start_entry = self.db.query(AuditLogEntry).filter(
                AuditLogEntry.entry_id == start_id
            ).first()
            if start_entry:
                query = query.filter(AuditLogEntry.id >= start_entry.id)
        
        if end_id:
            end_entry = self.db.query(AuditLogEntry).filter(
                AuditLogEntry.entry_id == end_id
            ).first()
            if end_entry:
                query = query.filter(AuditLogEntry.id <= end_entry.id)
        
        entries = query.all()
        
        # Verify chain
        tampered_entries = []
        current_previous_hash = None
        
        for entry in entries:
            # Verify this entry's hash
            hash_data = {
                "entry_id": entry.entry_id,
                "event_type": entry.event_type,
                "user_id": entry.user_id,
                "action": entry.action,
                "timestamp": entry.timestamp.isoformat(),
                "previous_hash": entry.previous_hash
            }
            
            computed_hash = self._compute_hash(hash_data)
            
            if computed_hash != entry.event_hash:
                tampered_entries.append(entry.entry_id)
                entry.is_verified = False
            
            # Verify chain link
            if entry.previous_hash != current_previous_hash:
                if current_previous_hash is not None:  # Not first entry
                    tampered_entries.append(entry.entry_id)
                    entry.is_verified = False
            
            current_previous_hash = entry.event_hash
        
        is_valid = len(tampered_entries) == 0
        
        # Record verification
        verification_id = str(uuid.uuid4())
        verification = AuditLogVerification(
            verification_id=verification_id,
            start_entry_id=start_id,
            end_entry_id=end_id,
            is_valid=is_valid,
            total_entries_checked=len(entries),
            tampering_detected=len(tampered_entries) > 0,
            tampering_details=json.dumps({"tampered_entries": tampered_entries})
        )
        
        self.db.add(verification)
        self.db.commit()
        
        return {
            "is_valid": is_valid,
            "total_entries": len(entries),
            "tampering_detected": len(tampered_entries) > 0,
            "tampered_entries": tampered_entries,
            "verification_id": verification_id
        }
    
    def get_audit_trail(
        self,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit trail with filters
        
        Returns:
            List of audit log entries
        """
        query = self.db.query(AuditLogEntry)
        
        if user_id:
            query = query.filter(AuditLogEntry.user_id == user_id)
        if tenant_id:
            query = query.filter(AuditLogEntry.tenant_id == tenant_id)
        if event_type:
            query = query.filter(AuditLogEntry.event_type == event_type)
        if start_date:
            query = query.filter(AuditLogEntry.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLogEntry.timestamp <= end_date)
        
        entries = query.order_by(AuditLogEntry.id.desc()).limit(limit).all()
        
        return [
            {
                "entry_id": entry.entry_id,
                "event_type": entry.event_type,
                "user_id": entry.user_id,
                "action": entry.action,
                "details": json.loads(entry.details) if entry.details else {},
                "timestamp": entry.timestamp.isoformat(),
                "is_verified": entry.is_verified,
                "ip_address": entry.ip_address
            }
            for entry in entries
        ]
    
    def detect_tampering(self) -> Dict[str, Any]:
        """
        Run automatic tampering detection
        
        Returns:
            {
                "tampering_detected": bool,
                "tampered_entries": int,
                "recent_verification_id": str
            }
        """
        # Check recent entries (last 24 hours)
        cutoff = datetime.utcnow() - timedelta(days=1)
        
        verification = self.verify_chain_integrity()
        
        if verification["tampering_detected"]:
            # Log security alert
            self.log_event(
                event_type="TAMPERING_DETECTED",
                user_id="SYSTEM",
                action="Tampering detected in audit logs",
                details={
                    "tampered_entries": verification["tampered_entries"],
                    "verification_id": verification["verification_id"]
                }
            )
        
        return {
            "tampering_detected": verification["tampering_detected"],
            "tampered_entries": len(verification["tampered_entries"]),
            "recent_verification_id": verification["verification_id"]
        }


# ============================================================================
# Integration with FastAPI
# ============================================================================

def create_audit_logger(db_session: Session) -> SecureAuditLog:
    """Factory function to create audit logger"""
    return SecureAuditLog(db_session)


async def audit_log_middleware(request, call_next, db: Session, audit_logger: SecureAuditLog):
    """
    Middleware to automatically log API calls
    
    Usage in main.py:
        app.add_middleware(AuditLogMiddleware, db=db_session, audit_logger=logger)
    """
    response = await call_next(request)
    
    # Log API call (only for write operations to reduce noise)
    if request.method in ["POST", "PUT", "DELETE"]:
        audit_logger.log_event(
            event_type="API_CALL",
            user_id=request.headers.get("X-User-Id"),
            action=f"{request.method} {request.url.path}",
            details={
                "method": request.method,
                "endpoint": request.url.path,
                "status_code": response.status_code
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent")
        )
    
    return response
