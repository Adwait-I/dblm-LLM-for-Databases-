"""
core/logging.py
---------------
Structured JSON logging configuration for QueryMind.
Sanitises sensitive fields so passwords / API keys are never logged.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Dict

from pythonjsonlogger import jsonlogger

from app.core.config import settings

# Fields that must never appear in logs
_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "api_key",
        "apikey",
        "token",
        "authorization",
        "database_url",
        "database_readonly_url",
    }
)


class _SanitisedJsonFormatter(jsonlogger.JsonFormatter):
    """JSON log formatter that strips sensitive fields from log records."""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["service"] = "querymind-backend"
        log_record["env"] = settings.app_env

        # Remove sensitive keys
        for key in list(log_record.keys()):
            if key.lower() in _SENSITIVE_KEYS:
                log_record[key] = "***REDACTED***"


def setup_logging() -> None:
    """Configure root logger with structured JSON output."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        _SanitisedJsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s"
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Silence overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger (always uses the root handler configured above)."""
    return logging.getLogger(name)
