"""
PRIORITY 4: Request/Response Monitoring Middleware

Logs all API requests and responses with:
- Request metadata (method, path, headers)
- Response status and timing
- Performance metrics
- Error tracking
"""

import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class RequestMetadata:
    """Request metadata for logging"""
    def __init__(self, request: Request):
        self.method = request.method
        self.path = request.url.path
        self.query_params = dict(request.query_params)
        self.headers = dict(request.headers)
        self.client_host = request.client.host if request.client else "unknown"
        self.timestamp = datetime.now()
    
    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "path": self.path,
            "query_params": self.query_params,
            "client": self.client_host,
            "timestamp": self.timestamp.isoformat(),
            "user_agent": self.headers.get("user-agent", "unknown")
        }


class ResponseMetadata:
    """Response metadata for logging"""
    def __init__(self, status_code: int, response_time_ms: float):
        self.status_code = status_code
        self.response_time_ms = response_time_ms
        self.timestamp = datetime.now()
    
    def to_dict(self) -> dict:
        return {
            "status_code": self.status_code,
            "response_time_ms": round(self.response_time_ms, 2),
            "timestamp": self.timestamp.isoformat()
        }


class RequestResponseLogger(BaseHTTPMiddleware):
    """Middleware to log all requests and responses"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health/status",
            "/health/heartbeat-status",
            "/health/metrics"
        ]
        self.service_monitor = None  # Will be set if imported
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response"""
        
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Capture request metadata
        request_metadata = RequestMetadata(request)
        
        # Start timing
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            response_time_ms = (time.time() - start_time) * 1000
            
            # Create response metadata
            response_metadata = ResponseMetadata(response.status_code, response_time_ms)
            
            # Log the request/response
            self._log_request_response(
                request_metadata,
                response_metadata,
                success=True
            )
            
            # Track metrics if monitor is available
            if self.service_monitor:
                service_name = self._extract_service_name(request.url.path)
                self.service_monitor.record_request(
                    service_name=service_name,
                    success=response.status_code < 400,
                    response_time_ms=response_time_ms
                )
            
            return response
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            # Log error
            self._log_request_error(
                request_metadata,
                response_time_ms,
                str(e)
            )
            
            # Track metrics if monitor is available
            if self.service_monitor:
                service_name = self._extract_service_name(request.url.path)
                self.service_monitor.record_request(
                    service_name=service_name,
                    success=False,
                    response_time_ms=response_time_ms,
                    error=str(e)
                )
            
            raise
    
    def _log_request_response(self, request: RequestMetadata, response: ResponseMetadata, success: bool) -> None:
        """Log successful request/response"""
        level = logging.INFO if success else logging.WARNING
        
        log_entry = {
            "event": "request_complete",
            "request": request.to_dict(),
            "response": response.to_dict(),
            "success": success
        }
        
        logger.log(level, json.dumps(log_entry))
    
    def _log_request_error(self, request: RequestMetadata, response_time_ms: float, error: str) -> None:
        """Log failed request"""
        log_entry = {
            "event": "request_error",
            "request": request.to_dict(),
            "response_time_ms": round(response_time_ms, 2),
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.error(json.dumps(log_entry))
    
    @staticmethod
    def _extract_service_name(path: str) -> str:
        """Extract service name from path"""
        # Extract first meaningful part of path
        parts = path.strip('/').split('/')
        if len(parts) > 0:
            return parts[0]
        return "api"
