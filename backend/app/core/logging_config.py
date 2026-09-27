import json
import logging
import sys
from copy import copy
from datetime import UTC, datetime

from app.core.context import action, request_id

UTC_TZ_SUFFIX = "+00:00"


def _format_timestamp(dt: datetime) -> str:
    return dt.isoformat(timespec="milliseconds").replace(UTC_TZ_SUFFIX, "Z")


class StructuredJSONFormatter(logging.Formatter):
    """
    Enterprise-grade JSON formatter for python logging.
    """

    def _fallback_format(self, record: logging.LogRecord) -> str:
        try:
            level = getattr(record, "levelname", "ERROR")
            module = getattr(record, "module", "unknown")
            fallback_log = {
                "timestamp": _format_timestamp(datetime.now(UTC)),
                "level": level,
                "request_id": request_id.get(),
                "module": module,
                "action": action.get(),
                "message": "Structured logging formatter failure.",
            }
            return json.dumps(fallback_log)
        except Exception:
            try:
                return json.dumps(
                    {
                        "timestamp": _format_timestamp(datetime.now(UTC)),
                        "level": "ERROR",
                        "message": "Critical structured logging failure.",
                    }
                )
            except Exception:
                return "Logging critical failure"

    def format(self, record: logging.LogRecord) -> str:
        try:
            # Format timestamp as ISO-8601 UTC string
            timestamp = _format_timestamp(datetime.fromtimestamp(record.created, UTC))

            # Resolve properties
            req_id = getattr(record, "request_id", None) or request_id.get()
            act = getattr(record, "action", None) or action.get()
            log_data = {
                "timestamp": timestamp,
                "level": record.levelname,
                "request_id": req_id,
                "module": record.module,
                "action": act,
                "message": record.getMessage(),
            }

            if record.exc_info:
                exception_type = record.exc_info[0]
                if exception_type:
                    log_data["exception_type"] = exception_type.__name__

            return json.dumps(log_data)
        except Exception:
            # Requirement 7: Logging failures must never interrupt business operations.
            return self._fallback_format(record)


class StructuredTextFormatter(logging.Formatter):
    """
    Console log formatter that injects request_id safely.
    """

    def format(self, record: logging.LogRecord) -> str:
        safe_record = copy(record)
        req_id = getattr(safe_record, "request_id", None) or request_id.get() or "N/A"
        safe_record.request_id = req_id
        safe_record.exc_info = None
        safe_record.exc_text = None
        safe_record.stack_info = None
        return super().format(safe_record)


def setup_logging():
    """Configure Python logging centrally."""
    import os

    root_logger = logging.getLogger()
    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []

    env = os.getenv("ENVIRONMENT", "development")
    log_format = os.getenv(
        "LOG_FORMAT", "text" if env in ("development", "local", "ci") else "json"
    )

    handler = logging.StreamHandler(sys.stdout)
    if log_format == "json":
        handler.setFormatter(StructuredJSONFormatter())
    else:
        # Standard human-readable console logging with correlation ID
        handler.setFormatter(
            StructuredTextFormatter(
                "[%(asctime)s] %(levelname)s in %(module)s [ReqId: %(request_id)s]: %(message)s"
            )
        )
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Propagate Uvicorn and FastAPI logs to the root logger to format them
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True
        if name == "uvicorn.access":
            uvicorn_logger.disabled = True


# Initialize logger named "itpa"
logger = logging.getLogger("itpa")
