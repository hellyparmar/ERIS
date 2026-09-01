"""
Structured Logging Configuration
JSON-formatted logs for production monitoring
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler
import traceback
import os


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    Compatible with ELK/Splunk/CloudWatch
    """
    
    def __init__(
        self,
        include_timestamp: bool = True,
        include_level: bool = True,
        include_logger: bool = True,
        include_path: bool = True,
        include_function: bool = True,
        extra_fields: Dict[str, Any] = None
    ):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        self.include_logger = include_logger
        self.include_path = include_path
        self.include_function = include_function
        self.extra_fields = extra_fields or {}
        
        # Service metadata
        self.service_name = os.getenv("SERVICE_NAME", "rdios-api")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.version = os.getenv("APP_VERSION", "6.0.0")
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {}
        
        # Timestamp
        if self.include_timestamp:
            log_data["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Level
        if self.include_level:
            log_data["level"] = record.levelname
            log_data["level_num"] = record.levelno
        
        # Logger name
        if self.include_logger:
            log_data["logger"] = record.name
        
        # Message
        log_data["message"] = record.getMessage()
        
        # Location
        if self.include_path:
            log_data["path"] = record.pathname
            log_data["line"] = record.lineno
            log_data["module"] = record.module
        
        if self.include_function:
            log_data["function"] = record.funcName
        
        # Service metadata
        log_data["service"] = self.service_name
        log_data["environment"] = self.environment
        log_data["version"] = self.version
        
        # Exception info
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Extra fields from record
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "levelname", "levelno",
                "pathname", "filename", "module", "exc_info", "exc_text",
                "stack_info", "lineno", "funcName", "created",
                "msecs", "relativeCreated", "thread", "threadName",
                "processName", "process", "message"
            ):
                try:
                    json.dumps(value)  # Check if serializable
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)
        
        # Add configured extra fields
        log_data.update(self.extra_fields)
        
        return json.dumps(log_data, default=str)


class RequestContextFilter(logging.Filter):
    """Add request context to log records"""
    
    def __init__(self):
        super().__init__()
        self.request_id = None
        self.user_id = None
        self.client_ip = None
    
    def set_context(
        self,
        request_id: Optional[str] = None,
        user_id: Optional[int] = None,
        client_ip: Optional[str] = None
    ):
        self.request_id = request_id
        self.user_id = user_id
        self.client_ip = client_ip
    
    def clear_context(self):
        self.request_id = None
        self.user_id = None
        self.client_ip = None
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = self.request_id
        record.user_id = self.user_id
        record.client_ip = self.client_ip
        return True


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    log_to_file: bool = False,
    log_file_path: str = "logs/app.log",
    max_file_size: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configure structured logging for the application
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON format (True for production)
        log_to_file: Also log to file
        log_file_path: Path to log file
        max_file_size: Max size before rotation
        backup_count: Number of backup files to keep
    
    Returns:
        Configured root logger
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(request_id)s]"
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_to_file:
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add context filter
    context_filter = RequestContextFilter()
    logger.addFilter(context_filter)
    
    # Store filter reference for context setting
    logger.context_filter = context_filter
    
    return logger


# Convenience loggers for different modules
def get_logger(name: str) -> logging.Logger:
    """Get a named logger"""
    return logging.getLogger(name)


# Pre-configured loggers
api_logger = get_logger("api")
ml_logger = get_logger("ml")
db_logger = get_logger("db")
auth_logger = get_logger("auth")
causal_logger = get_logger("causal")


# Logging middleware for FastAPI
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        
        # Set context
        logger = logging.getLogger()
        if hasattr(logger, 'context_filter'):
            logger.context_filter.set_context(
                request_id=request_id,
                client_ip=client_ip
            )
        
        # Log request
        start_time = time.time()
        
        api_logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent", ""),
                "event": "request_start"
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log response
            duration = time.time() - start_time
            
            api_logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "event": "request_complete"
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            api_logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                    "event": "request_error"
                },
                exc_info=True
            )
            raise
        
        finally:
            # Clear context
            if hasattr(logger, 'context_filter'):
                logger.context_filter.clear_context()
