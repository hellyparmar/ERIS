import logging
import os
import sys
import json
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from app.config import settings

# Ensure logs directory exists
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, "app.log")

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for production logs."""
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra"):
            log_record.update(record.extra)
            
        return json.dumps(log_record)

def setup_logging():
    """Configure structured logging."""
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)
    
    # Avoid duplicate handlers if already setup
    if logger.handlers:
        return logger
        
    # console handler (Pretty format for dev)
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.DEBUG:
        console_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )
    else:
        console_format = JSONFormatter()
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (JSON format with daily rotation)
    file_handler = TimedRotatingFileHandler(
        LOG_FILE, 
        when="midnight", 
        interval=1, 
        backupCount=30,
        encoding="utf-8"
    )
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    return logger

# Initialize logger
logger = setup_logging()
