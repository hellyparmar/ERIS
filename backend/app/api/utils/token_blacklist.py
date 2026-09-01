"""
JWT Token Revocation & Blacklist
Handles token logout and invalidation
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Set
import redis
import os

logger = logging.getLogger(__name__)

# Redis for distributed token blacklist
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    logger.warning(f"Redis not available for token blacklist: {e}. Using in-memory fallback.")
    redis_client = None

# In-memory fallback (for dev/testing)
_token_blacklist: Set[str] = set()
_blacklist_expiry: Dict[str, datetime] = {}


class TokenBlacklist:
    """Manage token revocation and blacklist"""
    
    @staticmethod
    def revoke_token(token: str, expires_at: datetime) -> bool:
        """
        Revoke a token by adding it to blacklist
        
        Args:
            token: JWT token to revoke
            expires_at: When token would naturally expire (for cleanup)
        
        Returns:
            True if revocation successful
        """
        try:
            if redis_client:
                # Calculate TTL (how long until token expires)
                ttl = int((expires_at - datetime.utcnow()).total_seconds())
                if ttl > 0:
                    # Store in Redis with automatic expiry
                    redis_client.setex(f"blacklist:{token}", ttl, "revoked")
                    logger.info(f"Token revoked (Redis, TTL: {ttl}s)")
                    return True
            else:
                # In-memory fallback
                _token_blacklist.add(token)
                _blacklist_expiry[token] = expires_at
                logger.info(f"Token revoked (in-memory)")
                return True
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False
    
    @staticmethod
    def is_blacklisted(token: str) -> bool:
        """
        Check if token is revoked
        
        Args:
            token: JWT token to check
        
        Returns:
            True if token is blacklisted/revoked
        """
        try:
            if redis_client:
                # Check Redis
                exists = redis_client.exists(f"blacklist:{token}")
                return bool(exists)
            else:
                # In-memory check + cleanup
                if token in _token_blacklist:
                    # Check if still valid (not expired)
                    expiry = _blacklist_expiry.get(token)
                    if expiry and expiry > datetime.utcnow():
                        return True
                    else:
                        # Cleanup expired entries
                        _token_blacklist.discard(token)
                        _blacklist_expiry.pop(token, None)
                return False
        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            return False
    
    @staticmethod
    def logout_user(token: str, expires_at: datetime) -> Dict[str, str]:
        """
        Logout user by revoking their token
        
        Args:
            token: JWT token to revoke
            expires_at: Token expiration time
        
        Returns:
            Dict with logout status
        """
        success = TokenBlacklist.revoke_token(token, expires_at)
        return {
            "status": "logged_out" if success else "logout_failed",
            "message": "Token revoked successfully" if success else "Failed to revoke token"
        }
    
    @staticmethod
    def cleanup_expired() -> int:
        """
        Clean up expired tokens from in-memory blacklist
        (Redis handles this automatically)
        
        Returns:
            Number of entries cleaned
        """
        if redis_client:
            return 0  # Redis handles cleanup automatically
        
        now = datetime.utcnow()
        expired = [t for t, exp in _blacklist_expiry.items() if exp <= now]
        
        for token in expired:
            _token_blacklist.discard(token)
            _blacklist_expiry.pop(token, None)
        
        logger.info(f"Cleaned up {len(expired)} expired tokens from blacklist")
        return len(expired)
    
    @staticmethod
    def get_blacklist_size() -> int:
        """Get current size of blacklist"""
        if redis_client:
            try:
                count = redis_client.dbsize()
                return count
            except:
                return -1
        else:
            return len(_token_blacklist)


# Export for use in auth middleware
token_blacklist = TokenBlacklist()


# Convenience functions for simpler API
def revoke_token(token: str, token_expiry: datetime = None) -> bool:
    """
    Revoke a token immediately
    
    Args:
        token: JWT token string
        token_expiry: Unix timestamp when token expires (optional)
    
    Returns:
        True if successful
    """
    expiry = token_expiry or (datetime.utcnow() + timedelta(days=1))
    if isinstance(token_expiry, (int, float)):
        # Convert Unix timestamp to datetime
        from datetime import timezone
        expiry = datetime.fromtimestamp(token_expiry, tz=timezone.utc)
    
    return TokenBlacklist.revoke_token(token, expiry)


def is_token_revoked(token: str) -> bool:
    """
    Check if token is revoked
    
    Args:
        token: JWT token string
    
    Returns:
        True if revoked, False otherwise
    """
    return TokenBlacklist.is_blacklisted(token)


def get_blacklist_stats() -> dict:
    """Get blacklist statistics"""
    return {
        "total_revoked": TokenBlacklist.get_blacklist_size(),
        "timestamp": datetime.utcnow().isoformat()
    }


class LogoutService:
    """Service to handle user logout with token revocation"""
    
    @staticmethod
    def logout(token: str, token_expiry=None) -> dict:
        """
        Logout user by revoking their token
        
        Args:
            token: JWT token string
            token_expiry: Token expiry time (optional)
        
        Returns:
            Dictionary with logout status
        """
        expiry = token_expiry or (datetime.utcnow() + timedelta(days=1))
        if isinstance(token_expiry, (int, float)):
            from datetime import timezone
            expiry = datetime.fromtimestamp(token_expiry, tz=timezone.utc)
        
        success = TokenBlacklist.revoke_token(token, expiry)
        
        return {
            "status": "success" if success else "failed",
            "message": "Successfully logged out" if success else "Logout failed",
            "token_revoked": success
        }
    
    @staticmethod
    def verify_active(token: str) -> dict:
        """
        Verify if token is still active (not revoked)
        
        Args:
            token: JWT token string
        
        Returns:
            Dictionary with token status
        """
        revoked = TokenBlacklist.is_blacklisted(token)
        
        return {
            "token_active": not revoked,
            "token_revoked": revoked,
            "status": "revoked" if revoked else "active"
        }
