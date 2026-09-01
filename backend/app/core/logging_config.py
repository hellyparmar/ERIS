"""
Structured logging configuration for R-DIOS API.

In production, logs are JSON formatted for easier parsing and analysis.
In development, logs are human-readable with color coding.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Optional


class CustomJsonFormatter(logging.Formatter):
    """
    JSON formatter that includes additional context fields
    for production environments.
    """
    
    def format(self, record):
        """Format log record as JSON with additional fields"""
        log_dict = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage()
        }
        
        # Add context fields if available
        if hasattr(record, 'request_id') and getattr(record, 'request_id', None):
            log_dict['request_id'] = getattr(record, 'request_id')
        if hasattr(record, 'user_id') and getattr(record, 'user_id', None):
            log_dict['user_id'] = getattr(record, 'user_id')
        
        return json.dumps(log_dict)


class DevelopmentFormatter(logging.Formatter):
    """
    Development formatter with colors and human-readable format.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        
        # Format with timestamp, level, module, message
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        
        message = (
            f"{log_color}[{timestamp}] {record.levelname:8} "
            f"{record.module}.{record.funcName}:{record.lineno} - "
            f"{record.getMessage()}{self.COLORS['RESET']}"
        )
        
        return message


def setup_logging(environment: str = "development") -> None:
    """
    Configure logging for the application.
    
    Args:
        environment: "development" or "production"
        
    In development: Human-readable logs to console
    In production: JSON formatted logs for log aggregation services
    """
    root_logger = logging.getLogger()
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set root logger level
    root_logger.setLevel(logging.DEBUG)
    
    if environment == "production":
        # JSON logging for production
        json_handler = logging.StreamHandler(sys.stdout)
        json_handler.setLevel(logging.INFO)
        json_formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(module)s %(function)s %(message)s'
        )
        json_handler.setFormatter(json_formatter)
        root_logger.addHandler(json_handler)
        
        # Separate error handler for errors
        error_handler = logging.StreamHandler(sys.stderr)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(json_formatter)
        root_logger.addHandler(error_handler)
        
    else:
        # Development logging with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        dev_formatter = DevelopmentFormatter()
        console_handler.setFormatter(dev_formatter)
        root_logger.addHandler(console_handler)
    
    # Suppress noisy loggers
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Log startup info
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured for {environment} environment")


def get_logger_with_context(
    name: str,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> logging.LoggerAdapter:
    """
    Get a logger with request and user context.
    
    Useful for adding request_id and user_id to all logs from a specific context.
    
    Usage:
        logger = get_logger_with_context(__name__, request_id="123", user_id="456")
        logger.info("Something happened")
        # Will include request_id and user_id in the JSON output
    """
    logger = logging.getLogger(name)
    
    context = {}
    if request_id:
        context['request_id'] = request_id
    if user_id:
        context['user_id'] = user_id
    
    return logging.LoggerAdapter(logger, context)
