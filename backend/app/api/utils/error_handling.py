"""
Standardized Error Handling
Consistent error responses across the API
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Any, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import logging
import traceback
import os

logger = logging.getLogger(__name__)


@dataclass
class ErrorResponse:
    """Standardized error response structure"""
    error: str
    message: str
    code: str
    timestamp: str
    path: Optional[str] = None
    request_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        # Remove None values
        return {k: v for k, v in result.items() if v is not None}


class ErrorCodes:
    """Standard error codes"""
    # Authentication
    AUTH_INVALID_CREDENTIALS = "AUTH_001"
    AUTH_TOKEN_EXPIRED = "AUTH_002"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_003"
    AUTH_INVALID_TOKEN = "AUTH_004"
    
    # Validation
    VALIDATION_ERROR = "VAL_001"
    VALIDATION_MISSING_FIELD = "VAL_002"
    VALIDATION_INVALID_FORMAT = "VAL_003"
    
    # Resource
    RESOURCE_NOT_FOUND = "RES_001"
    RESOURCE_ALREADY_EXISTS = "RES_002"
    RESOURCE_CONFLICT = "RES_003"
    
    # Business Logic
    BUSINESS_INSUFFICIENT_STOCK = "BIZ_001"
    BUSINESS_CREDIT_LIMIT_EXCEEDED = "BIZ_002"
    BUSINESS_OPERATION_NOT_ALLOWED = "BIZ_003"
    
    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_001"
    
    # Server
    INTERNAL_ERROR = "SRV_001"
    SERVICE_UNAVAILABLE = "SRV_002"
    EXTERNAL_SERVICE_ERROR = "SRV_003"


class APIException(Exception):
    """Base API exception with standardized response"""
    
    def __init__(
        self,
        message: str,
        code: str = ErrorCodes.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[Dict] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class AuthenticationError(APIException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code=ErrorCodes.AUTH_INVALID_CREDENTIALS,
            status_code=401,
            details=details
        )


class AuthorizationError(APIException):
    """Insufficient permissions"""
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code=ErrorCodes.AUTH_INSUFFICIENT_PERMISSIONS,
            status_code=403,
            details=details
        )


class NotFoundError(APIException):
    """Resource not found"""
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} not found",
            code=ErrorCodes.RESOURCE_NOT_FOUND,
            status_code=404,
            details={"resource": resource, "identifier": str(identifier)}
        )


class ValidationError(APIException):
    """Validation error"""
    def __init__(self, message: str, field: str = None, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code=ErrorCodes.VALIDATION_ERROR,
            status_code=422,
            details={"field": field, **(details or {})}
        )


class BusinessLogicError(APIException):
    """Business rule violation"""
    def __init__(self, message: str, code: str = ErrorCodes.BUSINESS_OPERATION_NOT_ALLOWED, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code=code,
            status_code=400,
            details=details
        )


class RateLimitError(APIException):
    """Rate limit exceeded"""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            code=ErrorCodes.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details={"retry_after": retry_after}
        )


def create_error_response(
    error: str,
    message: str,
    code: str,
    request: Optional[Request] = None,
    details: Optional[Dict] = None
) -> ErrorResponse:
    """Create standardized error response"""
    return ErrorResponse(
        error=error,
        message=message,
        code=code,
        timestamp=datetime.utcnow().isoformat() + "Z",
        path=str(request.url.path) if request else None,
        request_id=request.headers.get("X-Request-ID") if request else None,
        details=details
    )


# Exception handlers for FastAPI

async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle custom API exceptions"""
    logger.warning(
        f"API Exception: {exc.code} - {exc.message}",
        extra={"code": exc.code, "details": exc.details}
    )
    
    response = create_error_response(
        error=exc.__class__.__name__,
        message=exc.message,
        code=exc.code,
        request=request,
        details=exc.details
    )
    
    headers = {}
    if isinstance(exc, RateLimitError):
        headers["Retry-After"] = str(exc.details.get("retry_after", 60))
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.to_dict(),
        headers=headers
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    code_map = {
        400: ErrorCodes.VALIDATION_ERROR,
        401: ErrorCodes.AUTH_INVALID_TOKEN,
        403: ErrorCodes.AUTH_INSUFFICIENT_PERMISSIONS,
        404: ErrorCodes.RESOURCE_NOT_FOUND,
        429: ErrorCodes.RATE_LIMIT_EXCEEDED,
        500: ErrorCodes.INTERNAL_ERROR
    }
    
    response = create_error_response(
        error="HTTPException",
        message=str(exc.detail),
        code=code_map.get(exc.status_code, ErrorCodes.INTERNAL_ERROR),
        request=request
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.to_dict()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    response = create_error_response(
        error="ValidationError",
        message="Request validation failed",
        code=ErrorCodes.VALIDATION_ERROR,
        request=request,
        details={"errors": errors}
    )
    
    return JSONResponse(
        status_code=422,
        content=response.to_dict()
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    # Log full traceback
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={"path": request.url.path}
    )
    
    # Don't expose internal errors in production
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    
    if is_production:
        message = "An internal error occurred. Please try again later."
        details = None
    else:
        message = str(exc)
        details = {"traceback": traceback.format_exc().split("\n")}
    
    response = create_error_response(
        error="InternalServerError",
        message=message,
        code=ErrorCodes.INTERNAL_ERROR,
        request=request,
        details=details
    )
    
    return JSONResponse(
        status_code=500,
        content=response.to_dict()
    )


def register_exception_handlers(app):
    """Register all exception handlers with FastAPI app"""
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Registered standardized exception handlers")
