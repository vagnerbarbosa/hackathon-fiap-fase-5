"""Configuração de logging JSON estruturado."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict

from src.core.config import settings


class JSONFormatter(logging.Formatter):
    """Formatador JSON customizado para logging estruturado."""

    def format(self, record: logging.LogRecord) -> str:
        """Formata registro de log como JSON.

        Args:
            record: Registro de log a ser formatado.

        Returns:
            str: Entrada de log formatada em JSON.
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

        # Add extra fields from record (passed via extra= in logging call)
        # Standard logging extras are stored in record.__dict__
        standard_keys = {"name", "msg", "args", "levelname", "levelno", "pathname", "filename",
                        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
                        "created", "msecs", "relativeCreated", "thread", "threadName",
                        "processName", "process", "request_id", "message", "asctime", "exception"}
        extra_fields = {k: v for k, v in record.__dict__.items() if k not in standard_keys}
        log_data.update(extra_fields)

        return json.dumps(log_data, default=str)


def setup_logging() -> None:
    """Configura logging da aplicação com formatador JSON.

    Configura o logger raiz com saída JSON para stdout.
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
    """Obtém instância de logger com o nome dado.

    Args:
        name: Nome do logger (tipicamente __name__).

    Returns:
        logging.Logger: Instância do logger.
    """
    return logging.getLogger(name)


class RequestIdFilter(logging.Filter):
    """Filtro que adiciona request_id aos registros de log."""

    def __init__(self, request_id: str = ""):
        super().__init__()
        self.request_id = request_id

    def filter(self, record: logging.LogRecord) -> bool:
        """Adiciona request_id ao registro."""
        record.request_id = self.request_id  # type: ignore
        return True
