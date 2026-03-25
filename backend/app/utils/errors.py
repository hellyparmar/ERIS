from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger("app")

class AppException(Exception):
    """Base exception for the application."""
    def __init__(
        self, 
        code: str, 
        message: str, 
        status_code: int = 500, 
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"

class ValidationError(AppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("VALIDATION_ERROR", message, 400, details)

class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__("AUTHENTICATION_ERROR", message, 401, details)

class PermissionError(AppException):
    def __init__(self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__("PERMISSION_DENIED", message, 403, details)

class NotFoundError(AppException):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            "NOT_FOUND", 
            f"{resource} with identifier {identifier} not found", 
            404
        )

class DatabaseError(AppException):
    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__("DATABASE_ERROR", message, 500, details)

async def app_exception_handler(request: Request, exc: AppException):
    """Handler for custom AppException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": exc.timestamp
            }
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler for standard FastAPI HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": {},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """Fallback handler for unhandled exceptions."""
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {"exception": str(exc)} if logging.DEBUG else {},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )
