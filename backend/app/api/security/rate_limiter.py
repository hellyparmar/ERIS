"""
Distributed Rate Limiting

Implements per-endpoint rate limiting to prevent:
- Brute force attacks on login endpoint
- API abuse and DDoS attacks
- Excessive database load from single user
- Excessive database load from single IP

Features:
- Per-user rate limiting
- Per-IP rate limiting
- Endpoint-specific limits
- Token bucket algorithm
- Redis-backed for distributed systems
- Graceful degradation if Redis unavailable
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Rate Limit Configuration
# ============================================================================

@dataclass
class RateLimit:
    """Rate limit configuration"""
    requests: int  # Number of requests
    window_seconds: int  # Time window in seconds
    
    def get_rate_string(self) -> str:
        """Human readable rate limit"""
        return f"{self.requests} req/{self.window_seconds}s"


class RateLimitPreset(str, Enum):
    """Predefined rate limit presets"""
    STRICT = "strict"  # 10 req/min - login, sensitive endpoints
    MODERATE = "moderate"  # 60 req/min - normal endpoints
    GENEROUS = "generous"  # 300 req/min - public endpoints
    UNLIMITED = "unlimited"  # No limits


PRESET_LIMITS = {
    RateLimitPreset.STRICT: RateLimit(requests=10, window_seconds=60),
    RateLimitPreset.MODERATE: RateLimit(requests=60, window_seconds=60),
    RateLimitPreset.GENEROUS: RateLimit(requests=300, window_seconds=60),
    RateLimitPreset.UNLIMITED: RateLimit(requests=999999, window_seconds=60),
}

# Endpoint-specific rate limits
ENDPOINT_LIMITS = {
    # Authentication - STRICT
    "/auth/login": RateLimitPreset.STRICT,
    "/auth/register": RateLimitPreset.STRICT,
    "/auth/forgot-password": RateLimitPreset.STRICT,
    
    # Sensitive operations - STRICT
    "/api/v1/pos/sale": RateLimitPreset.MODERATE,  # Important but not sensitive
    "/api/v1/invoice/create": RateLimitPreset.MODERATE,
    "/api/v1/credit/accounts/create": RateLimitPreset.MODERATE,
    
    # Read operations - GENEROUS
    "/api/v1/pos/receipt": RateLimitPreset.GENEROUS,
    "/api/v1/inventory/scan": RateLimitPreset.GENEROUS,
    "/api/v1/loyalty/balance": RateLimitPreset.GENEROUS,
    
    # Default - MODERATE
    "default": RateLimitPreset.MODERATE,
}


# ============================================================================
# In-Memory Rate Limiter (Local)
# ============================================================================

class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter (good for single-process development)
    
    For production, use RedisRateLimiter instead
    """
    
    def __init__(self):
        # Dictionary to store request timestamps
        # Key: f"{identifier}:{endpoint}"
        # Value: list of timestamps
        self.requests = defaultdict(list)
    
    def check_rate_limit(
        self,
        identifier: str,
        endpoint: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed under rate limit
        
        Returns:
            (is_allowed, info_dict)
        """
        preset = ENDPOINT_LIMITS.get(endpoint, ENDPOINT_LIMITS["default"])
        limit = PRESET_LIMITS[preset]
        
        key = f"{identifier}:{endpoint}"
        now = time.time()
        
        # Remove old requests outside the window
        self.requests[key] = [
            ts for ts in self.requests[key]
            if now - ts < limit.window_seconds
        ]
        
        current_count = len(self.requests[key])
        is_allowed = current_count < limit.requests
        
        if is_allowed:
            self.requests[key].append(now)
        
        return is_allowed, {
            "current_requests": current_count,
            "limit": limit.requests,
            "window_seconds": limit.window_seconds,
            "remaining": max(0, limit.requests - current_count - (1 if is_allowed else 0)),
            "reset_at": (now + limit.window_seconds)
        }
    
    def get_remaining_quota(
        self,
        identifier: str,
        endpoint: str
    ) -> Dict[str, int]:
        """Get remaining quota for identifier"""
        preset = ENDPOINT_LIMITS.get(endpoint, ENDPOINT_LIMITS["default"])
        limit = PRESET_LIMITS[preset]
        
        key = f"{identifier}:{endpoint}"
        now = time.time()
        
        # Remove old requests
        self.requests[key] = [
            ts for ts in self.requests[key]
            if now - ts < limit.window_seconds
        ]
        
        current_count = len(self.requests[key])
        
        return {
            "remaining": max(0, limit.requests - current_count),
            "limit": limit.requests,
            "reset_in_seconds": limit.window_seconds
        }


# ============================================================================
# Redis-backed Rate Limiter (Production)
# ============================================================================

class RedisRateLimiter:
    """
    Production-grade distributed rate limiter using Redis
    
    Implements token bucket algorithm for smooth rate limiting
    """
    
    def __init__(self, redis_client):
        """
        Initialize Redis rate limiter
        
        Args:
            redis_client: Redis connection client
        """
        self.redis = redis_client
    
    def check_rate_limit(
        self,
        identifier: str,
        endpoint: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed under rate limit
        
        Uses token bucket algorithm:
        - Bucket fills with tokens at fixed rate
        - Each request consumes 1 token
        - If bucket empty, request denied
        """
        preset = ENDPOINT_LIMITS.get(endpoint, ENDPOINT_LIMITS["default"])
        limit = PRESET_LIMITS[preset]
        
        key = f"rate_limit:{identifier}:{endpoint}"
        
        try:
            now = time.time()
            
            # Get current bucket state
            bucket_data = self.redis.get(key)
            
            if bucket_data:
                data = json.loads(bucket_data)
                tokens = data["tokens"]
                last_updated = data["last_updated"]
            else:
                tokens = limit.requests
                last_updated = now
            
            # Calculate tokens added since last update
            time_passed = now - last_updated
            tokens_added = time_passed * (limit.requests / limit.window_seconds)
            tokens = min(limit.requests, tokens + tokens_added)
            
            # Check if request allowed
            is_allowed = tokens >= 1
            
            if is_allowed:
                tokens -= 1
            
            # Update bucket
            self.redis.setex(
                key,
                limit.window_seconds * 2,  # Expire after 2 windows
                json.dumps({
                    "tokens": tokens,
                    "last_updated": now,
                    "limit": limit.requests
                })
            )
            
            remaining = int(tokens)
            
            return is_allowed, {
                "current_requests": limit.requests - remaining,
                "limit": limit.requests,
                "window_seconds": limit.window_seconds,
                "remaining": remaining,
                "reset_in_seconds": limit.window_seconds
            }
            
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # Degrade gracefully - allow request if Redis fails
            return True, {
                "degraded": True,
                "message": "Rate limiter unavailable, request allowed"
            }
    
    def get_remaining_quota(
        self,
        identifier: str,
        endpoint: str
    ) -> Dict[str, int]:
        """Get remaining quota"""
        is_allowed, info = self.check_rate_limit(identifier, endpoint)
        return {
            "remaining": info.get("remaining", 0),
            "limit": info.get("limit", 0),
            "reset_in_seconds": info.get("reset_in_seconds", 0)
        }


# ============================================================================
# Rate Limiter Factory
# ============================================================================

_rate_limiter = None

def init_rate_limiter(redis_client=None) -> None:
    """Initialize global rate limiter"""
    global _rate_limiter
    
    if redis_client:
        _rate_limiter = RedisRateLimiter(redis_client)
        logger.info("Initialized Redis-backed rate limiter")
    else:
        _rate_limiter = InMemoryRateLimiter()
        logger.warning("Using in-memory rate limiter (not suitable for production)")


def get_rate_limiter():
    """Get global rate limiter instance"""
    if _rate_limiter is None:
        init_rate_limiter()
    return _rate_limiter


# ============================================================================
# FastAPI Integration
# ============================================================================

from fastapi import Request, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting
    
    Usage in main.py:
        app.add_middleware(RateLimitMiddleware)
    """
    
    # Skip rate limiting for these paths
    SKIP_PATHS = {
        "/health",
        "/metrics",
        "/docs",
        "/openapi.json",
        "/redoc"
    }
    
    async def dispatch(self, request: Request, call_next):
        # Skip certain paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)
        
        # Get identifier (user ID or IP)
        identifier = (
            request.headers.get("X-User-Id") or
            request.headers.get("Authorization", "").split()[-1][:20] or  # Token prefix
            (request.client.host if request.client else "unknown")
        )
        
        # Check rate limit
        limiter = get_rate_limiter()
        is_allowed, info = limiter.check_rate_limit(identifier, request.url.path)
        
        # Add rate limit headers to response
        headers = {
            "X-RateLimit-Limit": str(info.get("limit", "unknown")),
            "X-RateLimit-Remaining": str(info.get("remaining", "unknown")),
            "X-RateLimit-Reset": str(int(info.get("reset_in_seconds", 60)))
        }
        
        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for {identifier} on {request.url.path}"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded: {info.get('limit')} requests per {info.get('window_seconds')} seconds",
                    "retry_after_seconds": info.get("reset_in_seconds")
                },
                headers={**headers, "Retry-After": str(info.get("reset_in_seconds"))}
            )
        
        response = await call_next(request)
        
        # Add headers to successful response
        for key, value in headers.items():
            response.headers[key] = value
        
        return response


# ============================================================================
# Dependency for endpoint-specific limits
# ============================================================================

async def check_rate_limit(request: Request):
    """
    Dependency for rate limiting in endpoints
    
    Usage:
        @router.post("/sensitive")
        async def sensitive_endpoint(
            rate_limit_check: None = Depends(check_rate_limit)
        ):
            ...
    """
    identifier = (
        request.headers.get("X-User-Id") or
        (request.client.host if request.client else "unknown")
    )
    
    limiter = get_rate_limiter()
    is_allowed, info = limiter.check_rate_limit(identifier, request.url.path)
    
    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {info['remaining']} requests remaining"
        )
