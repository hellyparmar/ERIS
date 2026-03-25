"""
API Key Management and Rotation
Secure API key generation, validation, and rotation
"""

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class APIKey:
    """API Key model"""
    key_id: str
    key_hash: str  # Hashed version of the key
    name: str
    created_at: str
    expires_at: Optional[str]
    last_used: Optional[str]
    permissions: List[str]
    is_active: bool
    rate_limit: int  # Requests per minute
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.fromisoformat(self.expires_at) < datetime.utcnow()


class APIKeyManager:
    """
    Secure API key management
    
    Features:
    - Secure key generation using secrets module
    - Key hashing for storage (never store plain keys)
    - Key rotation with grace period
    - Permission-based access control
    - Rate limiting per key
    """
    
    def __init__(self, storage_path: str = None):
        """
        Initialize API key manager
        
        Args:
            storage_path: Path to store API keys (use DB in production)
        """
        self.storage_path = storage_path or os.getenv(
            "API_KEYS_PATH",
            "data/api_keys.json"
        )
        self.keys: Dict[str, APIKey] = {}
        self._load_keys()
    
    def _load_keys(self):
        """Load API keys from storage"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for key_id, key_data in data.items():
                        self.keys[key_id] = APIKey(**key_data)
                logger.info(f"Loaded {len(self.keys)} API keys")
        except Exception as e:
            logger.warning(f"Could not load API keys: {e}")
    
    def _save_keys(self):
        """Save API keys to storage"""
        try:
            Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w') as f:
                data = {k: v.to_dict() for k, v in self.keys.items()}
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save API keys: {e}")
    
    @staticmethod
    def _generate_key() -> str:
        """Generate a secure API key"""
        # Format: rdios_live_xxxx...xxxx (32 bytes = 43 chars base64)
        return f"rdios_live_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def _hash_key(key: str) -> str:
        """Hash an API key for storage"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def create_key(
        self,
        name: str,
        permissions: List[str] = None,
        expires_in_days: int = None,
        rate_limit: int = 100
    ) -> Tuple[str, APIKey]:
        """
        Create a new API key
        
        Args:
            name: Human-readable name for the key
            permissions: List of allowed permissions
            expires_in_days: Days until expiration (None = never)
            rate_limit: Max requests per minute
        
        Returns:
            (plain_key, api_key_object)
        """
        # Generate key
        plain_key = self._generate_key()
        key_hash = self._hash_key(plain_key)
        key_id = f"key_{secrets.token_hex(8)}"
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = (datetime.utcnow() + timedelta(days=expires_in_days)).isoformat()
        
        # Create key object
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            created_at=datetime.utcnow().isoformat(),
            expires_at=expires_at,
            last_used=None,
            permissions=permissions or ["read"],
            is_active=True,
            rate_limit=rate_limit
        )
        
        # Store
        self.keys[key_id] = api_key
        self._save_keys()
        
        logger.info(f"Created API key: {key_id} for {name}")
        
        # Return plain key (only shown once!)
        return plain_key, api_key
    
    def validate_key(self, plain_key: str) -> Tuple[bool, Optional[APIKey], str]:
        """
        Validate an API key
        
        Args:
            plain_key: The plain text API key
        
        Returns:
            (is_valid, api_key_object, reason)
        """
        if not plain_key or not plain_key.startswith("rdios_"):
            return False, None, "Invalid key format"
        
        key_hash = self._hash_key(plain_key)
        
        # Find matching key
        for api_key in self.keys.values():
            if hmac.compare_digest(api_key.key_hash, key_hash):
                # Check if active
                if not api_key.is_active:
                    return False, api_key, "Key is deactivated"
                
                # Check expiration
                if api_key.is_expired():
                    return False, api_key, "Key has expired"
                
                # Update last used
                api_key.last_used = datetime.utcnow().isoformat()
                self._save_keys()
                
                return True, api_key, "Valid"
        
        return False, None, "Key not found"
    
    def rotate_key(
        self,
        key_id: str,
        grace_period_hours: int = 24
    ) -> Tuple[str, APIKey, APIKey]:
        """
        Rotate an API key
        
        Creates new key and keeps old one active for grace period
        
        Args:
            key_id: ID of key to rotate
            grace_period_hours: Hours to keep old key active
        
        Returns:
            (new_plain_key, new_api_key, old_api_key)
        """
        if key_id not in self.keys:
            raise ValueError(f"Key {key_id} not found")
        
        old_key = self.keys[key_id]
        
        # Create new key with same permissions
        new_plain_key, new_key = self.create_key(
            name=f"{old_key.name} (rotated)",
            permissions=old_key.permissions,
            rate_limit=old_key.rate_limit
        )
        
        # Set old key to expire after grace period
        old_key.expires_at = (
            datetime.utcnow() + timedelta(hours=grace_period_hours)
        ).isoformat()
        old_key.name = f"{old_key.name} (deprecated)"
        self._save_keys()
        
        logger.info(f"Rotated API key {key_id} -> {new_key.key_id}")
        
        return new_plain_key, new_key, old_key
    
    def revoke_key(self, key_id: str) -> bool:
        """Immediately revoke an API key"""
        if key_id not in self.keys:
            return False
        
        self.keys[key_id].is_active = False
        self._save_keys()
        
        logger.warning(f"Revoked API key: {key_id}")
        return True
    
    def list_keys(self, include_inactive: bool = False) -> List[Dict]:
        """List all API keys (without hashes)"""
        keys = []
        for api_key in self.keys.values():
            if not include_inactive and not api_key.is_active:
                continue
            
            key_info = api_key.to_dict()
            del key_info['key_hash']  # Never expose hash
            keys.append(key_info)
        
        return keys
    
    def has_permission(self, api_key: APIKey, permission: str) -> bool:
        """Check if key has permission"""
        if "admin" in api_key.permissions:
            return True
        return permission in api_key.permissions


# FastAPI dependency for API key authentication
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_key_manager: Optional[APIKeyManager] = None


def get_key_manager() -> APIKeyManager:
    """Get or create API key manager"""
    global _key_manager
    if _key_manager is None:
        _key_manager = APIKeyManager()
    return _key_manager


async def verify_api_key(
    api_key: str = Security(api_key_header),
    required_permission: str = "read"
) -> APIKey:
    """
    FastAPI dependency to verify API key
    
    Usage:
        @router.get("/data")
        async def get_data(api_key: APIKey = Depends(verify_api_key)):
            ...
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    manager = get_key_manager()
    is_valid, key_obj, reason = manager.validate_key(api_key)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid API key: {reason}",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if not manager.has_permission(key_obj, required_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {required_permission}"
        )
    
    return key_obj


# API Key management endpoints
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/admin/keys", tags=["API Key Management"])


@router.post("/create")
async def create_api_key(
    name: str,
    permissions: List[str] = ["read"],
    expires_in_days: int = None,
    rate_limit: int = 100
):
    """Create a new API key (admin only)"""
    manager = get_key_manager()
    plain_key, api_key = manager.create_key(
        name=name,
        permissions=permissions,
        expires_in_days=expires_in_days,
        rate_limit=rate_limit
    )
    
    return {
        "key": plain_key,  # Only shown once!
        "key_id": api_key.key_id,
        "name": api_key.name,
        "expires_at": api_key.expires_at,
        "permissions": api_key.permissions,
        "warning": "Save this key securely. It will not be shown again."
    }


@router.post("/{key_id}/rotate")
async def rotate_api_key(
    key_id: str,
    grace_period_hours: int = 24
):
    """Rotate an API key"""
    manager = get_key_manager()
    
    try:
        new_key, new_obj, old_obj = manager.rotate_key(key_id, grace_period_hours)
        return {
            "new_key": new_key,
            "new_key_id": new_obj.key_id,
            "old_key_id": old_obj.key_id,
            "old_key_expires": old_obj.expires_at,
            "warning": "Save the new key securely. Update your applications before the old key expires."
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{key_id}")
async def revoke_api_key(key_id: str):
    """Revoke an API key immediately"""
    manager = get_key_manager()
    
    if manager.revoke_key(key_id):
        return {"status": "revoked", "key_id": key_id}
    else:
        raise HTTPException(status_code=404, detail="Key not found")


@router.get("/")
async def list_api_keys(include_inactive: bool = False):
    """List all API keys"""
    manager = get_key_manager()
    return {"keys": manager.list_keys(include_inactive)}
