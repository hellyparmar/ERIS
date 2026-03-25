
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class APIRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter.
    Limits requests per IP address per minute.
    """
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        # Dictionary to store request timestamps per IP
        # Structure: {ip: [timestamp1, timestamp2, ...]}
        self._requests = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for static files or documentation
        if request.url.path.startswith(("/docs", "/redoc", "/static")):
            return await call_next(request)
            
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean up old timestamps (older than 1 minute)
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] 
            if current_time - t < 60
        ]
        
        # Check limit
        if len(self._requests[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return Response(
                content="{'error': 'Rate limit exceeded. Try again later.'}", 
                status_code=429,
                media_type="application/json"
            )
            
        # Add current request timestamp
        self._requests[client_ip].append(current_time)
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(self.requests_per_minute - len(self._requests[client_ip]))
        
        return response

# Singleton instance for backward compatibility
rate_limiter = APIRateLimitMiddleware(app=None, requests_per_minute=100)
