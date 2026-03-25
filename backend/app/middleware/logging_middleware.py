import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logging import logger

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract basic info
        # auth_header = request.headers.get("Authorization", "")
        # This part was reported as "Cannot index into str" by IDE if not careful
        # We'll use a safer approach for token extraction if needed.
        method = request.method
        path = request.url.path
        ip = request.client.host if request.client else "unknown"
        
        # Try to get user ID if already authenticated (might not be available yet in middleware)
        user_id = "anonymous"
        if hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", "unknown")
            
        # Log request start (Optional, might be too verbose)
        # logger.info(f"Request started: {method} {path} from {ip}")
        
        response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000
        status_code = response.status_code
        
        # Explicitly cast to float and round to satisfy picky type checkers
        duration = round(float(process_time), 2)
        
        # Structured log entry
        log_data = {
            "method": method,
            "path": path,
            "ip": ip,
            "user_id": user_id,
            "status_code": status_code,
            "duration_ms": duration,
        }
        
        if status_code >= 400:
            logger.error(f"Request failed: {method} {path} - {status_code}", extra=log_data)
        else:
            logger.info(f"Request completed: {method} {path} - {status_code}", extra=log_data)
            
        response.headers["X-Process-Time"] = str(process_time)
        return response
