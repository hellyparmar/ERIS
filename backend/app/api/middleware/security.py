"""
API Security Middleware
Provides Security Headers, IP Filtering, and Redis-backed Rate Limiting
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
import logging
import os
import json

logger = logging.getLogger(__name__)

# ----- IP Filtering Middleware -----

class IPFilterMiddleware(BaseHTTPMiddleware):
    """
    Blocks requests from blacklisted IPs.
    Allows only whitelisted IPs if whitelist is defined.
    """
    def __init__(self, app, whitelist=None, blacklist=None):
        super().__init__(app)
        self.whitelist = whitelist or set()
        self.blacklist = blacklist or set()

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else None
        
        if not client_ip:
            return await call_next(request)
            
        if self.blacklist and client_ip in self.blacklist:
            logger.warning(f"Blocked request from blacklisted IP: {client_ip}")
            return Response(
                content=json.dumps({"error": "Access denied"}),
                status_code=403,
                media_type="application/json"
            )
            
        if self.whitelist and client_ip not in self.whitelist:
            logger.warning(f"Blocked request from non-whitelisted IP: {client_ip}")
            return Response(
                content=json.dumps({"error": "Access denied"}),
                status_code=403,
                media_type="application/json"
            )
            
        return await call_next(request)


# ----- Security Headers Middleware -----

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds standard security headers to all HTTP responses (Helmet-style).
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


# ----- Enhanced Rate Limiter Middleware -----

class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Distributed Rate Limiter using Redis if available.
    Falls back to in-memory limiting if Redis is down/unavailable.
    """
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.limit = requests_per_minute
        self.use_redis = False
        self._memory_store = defaultdict(list)
        
        # Try connecting to Redis
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            from redis import Redis
            self.redis = Redis(host=redis_host, port=6379, socket_timeout=1, decode_responses=True)
            self.redis.ping()
            self.use_redis = True
            logger.info("Redis Rate Limiter initialized successfully.")
        except Exception as e:
            logger.warning(f"Redis unavailable, falling back to in-memory rate limiting: {e}")

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for static/docs
        if request.url.path.startswith(("/docs", "/redoc", "/static", "/health")):
            return await call_next(request)
            
        client_ip = request.client.host if request.client else "unknown"
        
        if self.use_redis:
            allowed, remaining = self._check_redis_limit(client_ip)
        else:
            allowed, remaining = self._check_memory_limit(client_ip)
            
        if not allowed:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return Response(
                content=json.dumps({"error": "Rate limit exceeded. Try again later."}), 
                status_code=429,
                media_type="application/json",
                headers={
                    "X-RateLimit-Limit": str(self.limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60"
                }
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    def _check_redis_limit(self, ip: str) -> tuple[bool, int]:
        """Check limit using Redis Sliding Window Log"""
        key = f"rate_limit:{ip}"
        now_ms = int(time.time() * 1000)
        window_start_ms = now_ms - 60000
        
        try:
            pipe = self.redis.pipeline()
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start_ms)
            # Add current request
            pipe.zadd(key, {str(now_ms): now_ms})
            # Count requests
            pipe.zcard(key)
            # Set expiry to keep redis clean
            pipe.expire(key, 60)
            
            results = pipe.execute()
            request_count = results[2]
            
            if request_count > self.limit:
                return False, 0
                
            return True, self.limit - request_count
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            self.use_redis = False  # Auto-fallback on failure
            return self._check_memory_limit(ip)

    def _check_memory_limit(self, ip: str) -> tuple[bool, int]:
        """Fallback in-memory rate limiting"""
        current_time = time.time()
        
        # Clean up old timestamps (older than 1 minute)
        self._memory_store[ip] = [
            t for t in self._memory_store[ip] 
            if current_time - t < 60
        ]
        
        if len(self._memory_store[ip]) >= self.limit:
            return False, 0
            
        self._memory_store[ip].append(current_time)
        return True, self.limit - len(self._memory_store[ip])
