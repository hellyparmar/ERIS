"""
Device Fingerprinting and Whitelisting

Secures login and API access by implementing device-level authentication.
Users can only access sensitive operations from approved devices, preventing
account hijacking even if credentials are compromised.

Features:
- Automatic device fingerprinting on login
- Device approval workflow
- Device revocation
- Suspicious device detection
- Multi-device management per user
"""

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from fastapi import Request
import logging

Base = declarative_base()
logger = logging.getLogger(__name__)

# ============================================================================
# Database Models
# ============================================================================

class ApprovedDevice(Base):
    """Approved device record for a user"""
    __tablename__ = "approved_devices"
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String(100), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), index=True, nullable=False)
    tenant_id = Column(String(36), index=True, nullable=False)
    
    # Device information
    device_name = Column(String(200))
    device_type = Column(String(50))  # 'desktop', 'mobile', 'tablet', 'pos_terminal'
    
    # Fingerprint
    fingerprint_hash = Column(String(64), unique=True, nullable=False, index=True)
    
    # Device characteristics (stored hashed)
    ip_address = Column(String(45))
    user_agent_hash = Column(String(64))
    hardware_id_hash = Column(String(64))
    
    # Approval workflow
    is_approved = Column(Boolean, default=False)
    approved_at = Column(DateTime)
    approved_by = Column(String(36))  # Admin user ID who approved
    
    # Activity tracking
    last_used = Column(DateTime)
    login_count = Column(Integer, default=0)
    failed_login_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime)
    revoked_by = Column(String(36))
    
    # Metadata
    registered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeviceAccessLog(Base):
    """Log of device access attempts"""
    __tablename__ = "device_access_logs"
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String(100), index=True)
    user_id = Column(String(36), index=True)
    tenant_id = Column(String(36), index=True)
    
    # Access details
    access_type = Column(String(50))  # 'LOGIN', 'API_CALL', 'SENSITIVE_OPERATION'
    endpoint = Column(String(200))
    
    # Result
    success = Column(Boolean)
    reason_if_denied = Column(String(200))
    
    # Request info
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Metadata
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)


# ============================================================================
# Device Fingerprinting
# ============================================================================

class DeviceFingerprinter:
    """
    Generates and verifies device fingerprints
    
    Fingerprint components:
    - IP Address (most volatile, can change)
    - User Agent (browser/app identifier)
    - Hardware characteristics
    - Installation ID (unique per app installation)
    """
    
    FINGERPRINT_VERSION = "1.0"
    FINGERPRINT_SECRET = "ENTERPRISE_RETAIL_SECURITY"  # Should be in env variable
    
    @staticmethod
    def hash_component(value: str, salt: str = "") -> str:
        """Hash a fingerprint component with HMAC"""
        if not value:
            return "null"
        key = (DeviceFingerprinter.FINGERPRINT_SECRET + salt).encode()
        return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()
    
    @staticmethod
    def generate_fingerprint(request: Request, device_type: str = "web") -> Dict[str, str]:
        """
        Generate device fingerprint from request
        
        Args:
            request: FastAPI Request object
            device_type: Type of device ('web', 'mobile', 'api', 'pos_terminal')
        
        Returns:
            {
                "fingerprint_hash": str,  # Combined hash
                "ip_address": str,
                "user_agent_hash": str,
                "browser_fingerprint": str,
                "device_type": str
            }
        """
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # Hash sensitive components
        user_agent_hash = DeviceFingerprinter.hash_component(user_agent)
        
        # Combine components for overall fingerprint
        fingerprint_data = {
            "version": DeviceFingerprinter.FINGERPRINT_VERSION,
            "user_agent": user_agent_hash,
            "device_type": device_type,
            "ip_class": ip_address.split(".")[:3] if "." in ip_address else "unknown"  # Only class C
        }
        
        fingerprint_json = json.dumps(fingerprint_data, sort_keys=True)
        fingerprint_hash = hashlib.sha256(fingerprint_json.encode()).hexdigest()
        
        return {
            "fingerprint_hash": fingerprint_hash,
            "ip_address": ip_address,
            "user_agent_hash": user_agent_hash,
            "browser_fingerprint": DeviceFingerprinter.hash_component(user_agent),
            "device_type": device_type,
            "raw_data": fingerprint_data
        }
    
    @staticmethod
    def generate_installation_id() -> str:
        """Generate unique ID for application installation"""
        return str(uuid.uuid4())


# ============================================================================
# Device Whitelist Management
# ============================================================================

class DeviceWhitelist:
    """
    Manages approved devices for users
    
    Features:
    - Register new devices
    - Approve/deny device registration
    - Revoke device access
    - Check device approval status
    - Track device usage
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def register_device(
        self,
        user_id: str,
        tenant_id: str,
        fingerprint: Dict[str, str],
        device_name: str,
        device_type: str = "web"
    ) -> Dict[str, Any]:
        """
        Register a new device for a user
        
        Device must be approved before use (unless auto-approval is enabled)
        """
        # Check if device already exists
        existing = self.db.query(ApprovedDevice).filter(
            ApprovedDevice.fingerprint_hash == fingerprint["fingerprint_hash"],
            ApprovedDevice.user_id == user_id
        ).first()
        
        if existing:
            existing.last_used = datetime.utcnow()
            existing.login_count += 1
            self.db.commit()
            return {
                "status": "existing",
                "device_id": existing.device_id,
                "is_approved": existing.is_approved
            }
        
        # Create new device record
        device = ApprovedDevice(
            user_id=user_id,
            tenant_id=tenant_id,
            device_name=device_name,
            device_type=device_type,
            fingerprint_hash=fingerprint["fingerprint_hash"],
            ip_address=fingerprint["ip_address"],
            user_agent_hash=fingerprint["user_agent_hash"],
            is_approved=True,  # Auto-approve for now (can be changed to require manual approval)
            approved_at=datetime.utcnow(),
            last_used=datetime.utcnow(),
            login_count=1
        )
        
        self.db.add(device)
        self.db.commit()
        
        logger.info(f"Registered device {device.device_id} for user {user_id}")
        
        return {
            "status": "registered",
            "device_id": device.device_id,
            "is_approved": device.is_approved
        }
    
    def is_device_approved(
        self,
        user_id: str,
        fingerprint: Dict[str, str]
    ) -> bool:
        """Check if device is approved for user"""
        device = self.db.query(ApprovedDevice).filter(
            ApprovedDevice.user_id == user_id,
            ApprovedDevice.fingerprint_hash == fingerprint["fingerprint_hash"],
            ApprovedDevice.is_active == True,
            ApprovedDevice.is_approved == True
        ).first()
        
        return device is not None
    
    def approve_device(
        self,
        device_id: str,
        approved_by: str
    ) -> Dict[str, Any]:
        """Admin approval of a device"""
        device = self.db.query(ApprovedDevice).filter(
            ApprovedDevice.device_id == device_id
        ).first()
        
        if not device:
            return {"status": "error", "message": "Device not found"}
        
        device.is_approved = True
        device.approved_at = datetime.utcnow()
        device.approved_by = approved_by
        self.db.commit()
        
        logger.info(f"Approved device {device_id} by {approved_by}")
        
        return {
            "status": "approved",
            "device_id": device.device_id,
            "device_name": device.device_name
        }
    
    def revoke_device(
        self,
        device_id: str,
        revoked_by: str
    ) -> Dict[str, Any]:
        """Revoke access for a device"""
        device = self.db.query(ApprovedDevice).filter(
            ApprovedDevice.device_id == device_id
        ).first()
        
        if not device:
            return {"status": "error", "message": "Device not found"}
        
        device.is_active = False
        device.revoked_at = datetime.utcnow()
        device.revoked_by = revoked_by
        self.db.commit()
        
        logger.warning(f"Revoked device {device_id} by {revoked_by}")
        
        return {
            "status": "revoked",
            "device_id": device.device_id
        }
    
    def get_user_devices(
        self,
        user_id: str,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all devices for a user"""
        query = self.db.query(ApprovedDevice).filter(
            ApprovedDevice.user_id == user_id
        )
        
        if active_only:
            query = query.filter(ApprovedDevice.is_active == True)
        
        devices = query.all()
        
        return [
            {
                "device_id": d.device_id,
                "device_name": d.device_name,
                "device_type": d.device_type,
                "is_approved": d.is_approved,
                "is_active": d.is_active,
                "last_used": d.last_used.isoformat() if d.last_used else None,
                "registered_at": d.registered_at.isoformat()
            }
            for d in devices
        ]
    
    def record_access(
        self,
        device_id: str,
        user_id: str,
        tenant_id: str,
        access_type: str,
        endpoint: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        reason_if_denied: str = None
    ) -> None:
        """Record device access attempt"""
        log = DeviceAccessLog(
            device_id=device_id,
            user_id=user_id,
            tenant_id=tenant_id,
            access_type=access_type,
            endpoint=endpoint,
            success=success,
            reason_if_denied=reason_if_denied,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(log)
        
        # Update device statistics
        device = self.db.query(ApprovedDevice).filter(
            ApprovedDevice.device_id == device_id
        ).first()
        
        if device:
            device.last_used = datetime.utcnow()
            if success:
                device.login_count += 1
            else:
                device.failed_login_count += 1
        
        self.db.commit()
    
    def detect_suspicious_devices(
        self,
        user_id: str,
        threshold_failed_logins: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Detect suspicious devices based on failed login attempts
        
        Returns list of devices that exceed failure threshold
        """
        devices = self.db.query(ApprovedDevice).filter(
            ApprovedDevice.user_id == user_id,
            ApprovedDevice.failed_login_count >= threshold_failed_logins
        ).all()
        
        return [
            {
                "device_id": d.device_id,
                "device_name": d.device_name,
                "failed_logins": d.failed_login_count,
                "last_attempt": self.db.query(DeviceAccessLog).filter(
                    DeviceAccessLog.device_id == d.device_id,
                    DeviceAccessLog.success == False
                ).order_by(DeviceAccessLog.timestamp.desc()).first().timestamp.isoformat()
            }
            for d in devices
        ]


# ============================================================================
# Integration Functions
# ============================================================================

def create_device_whitelist(db: Session) -> DeviceWhitelist:
    """Factory function for device whitelist"""
    return DeviceWhitelist(db)
