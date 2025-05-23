import json
import logging
import logging.handlers
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .config import ConfigManager, LoggingConfig

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }

        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data)

class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID if not present."""
        if not hasattr(record, "correlation_id"):
            record.correlation_id = str(uuid.uuid4())
        return True

class LogManager:
    """Manage logging configuration and setup."""
    
    def __init__(self, config: Optional[LoggingConfig] = None):
        self.config = config or ConfigManager().get_config().logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.config.level)

        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter())
        console_handler.addFilter(CorrelationFilter())
        root_logger.addHandler(console_handler)

        # Add file handler with rotation
        log_file = log_dir / "opmas.log"
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(log_file),
            when=self.config.rotation.split()[1],
            interval=int(self.config.rotation.split()[0]),
            backupCount=int(self.config.retention.split()[0])
        )
        file_handler.setFormatter(JSONFormatter())
        file_handler.addFilter(CorrelationFilter())
        root_logger.addHandler(file_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the specified name."""
        logger = logging.getLogger(name)
        logger.propagate = True
        return logger

def setup_logging(config: Optional[LoggingConfig] = None) -> None:
    """Set up logging configuration."""
    LogManager(config).get_logger(__name__) 