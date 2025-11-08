"""
Logging configuration with sensitive data masking.
All logs include correlation_id for request tracing.
"""

import logging
import re
from contextvars import ContextVar

correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")


class SensitiveDataFilter(logging.Filter):
    """Filter to mask sensitive data in logs"""

    PATTERNS = [
        (re.compile(r'"password"\s*:\s*"[^"]*"'), '"password":"***"'),
        (re.compile(r'"token"\s*:\s*"[^"]*"'), '"token":"***"'),
        (re.compile(r'"api_key"\s*:\s*"[^"]*"'), '"api_key":"***"'),
        (re.compile(r'"secret"\s*:\s*"[^"]*"'), '"secret":"***"'),
        (
            re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "***@***.***",
        ),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern, replacement in self.PATTERNS:
            message = pattern.sub(replacement, message)
        record.msg = message
        record.args = ()
        return True


class CorrelationIdFilter(logging.Filter):
    """Adds correlation_id to each log record"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_ctx.get() or "N/A"
        return True


def setup_logging() -> None:
    """Setup application logging"""
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s"
    )
    console_handler.setFormatter(formatter)

    console_handler.addFilter(SensitiveDataFilter())
    console_handler.addFilter(CorrelationIdFilter())

    logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Get logger with configured filters"""
    return logging.getLogger(f"app.{name}")
