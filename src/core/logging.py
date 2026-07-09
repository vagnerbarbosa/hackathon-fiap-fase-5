"""Structured JSON logging configuration."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict

from src.core.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format.

        Returns:
            str: JSON formatted log entry.
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }

        # Add request_id if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data, default=str)


def setup_logging() -> None:
    """Configure application logging with JSON formatter.

    Sets up root logger with JSON output to stdout.
    """
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Set SQLAlchemy logging level
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance with given name.

    Args:
        name: Logger name (typically __name__).

    Returns:
        logging.Logger: Logger instance.
    """
    return logging.getLogger(name)


class RequestIdFilter(logging.Filter):
    """Filter that adds request_id to log records."""

    def __init__(self, request_id: str = ""):
        super().__init__()
        self.request_id = request_id

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id to record."""
        record.request_id = self.request_id  # type: ignore
        return True
