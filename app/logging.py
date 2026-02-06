"""
AIBET Analytics Platform - Structured JSON Logging
"""

import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(name: str) -> logging.Logger:
    """Setup structured JSON logging"""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Set level
    log_level = logging.INFO
    logger.setLevel(log_level)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)
