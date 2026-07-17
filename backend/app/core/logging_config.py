import json
import logging
import sys
from datetime import UTC, datetime

from app.core.context import action, request_id, user_id


class StructuredJSONFormatter(logging.Formatter):
    """
    Enterprise-grade JSON formatter for python logging.
    """

    def format(self, record: logging.LogRecord) -> str:
        try:
            # Format timestamp as ISO-8601 UTC string
            timestamp = (
                datetime.fromtimestamp(record.created, UTC)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
            )

            # Resolve properties
            req_id = getattr(record, "request_id", None) or request_id.get()
            act = getattr(record, "action", None) or action.get()
            u_id = getattr(record, "user_id", None) or user_id.get()

            log_data = {
                "timestamp": timestamp,
                "level": record.levelname,
                "request_id": req_id,
                "module": record.module,
                "action": act,
                "user_id": u_id,
                "message": record.getMessage(),
            }

            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)

            # Retrieve any extra properties passed via extra={...}
            standard_attrs = {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "request_id",
                "action",
                "user_id",
            }
            extra_data = {
                k: v for k, v in record.__dict__.items() if k not in standard_attrs
            }
            if extra_data:
                log_data["extra"] = extra_data

            return json.dumps(log_data)
        except Exception as e:
            # Requirement 7: Logging failures must never interrupt business operations.
            try:
                level = getattr(record, "levelname", "ERROR")
                module = getattr(record, "module", "unknown")
                msg = "unknown message"
                if record is not None:
                    try:
                        msg = record.getMessage()
                    except Exception:
                        msg = str(getattr(record, "msg", "unknown message"))

                fallback_log = {
                    "timestamp": datetime.now(UTC)
                    .isoformat(timespec="milliseconds")
                    .replace("+00:00", "Z"),
                    "level": level,
                    "request_id": request_id.get(),
                    "module": module,
                    "action": action.get(),
                    "user_id": user_id.get(),
                    "message": (
                        f"Logging formatter failure: {str(e)}. Original message: {msg}"
                    ),
                }
                return json.dumps(fallback_log)
            except Exception as inner_e:
                try:
                    return json.dumps(
                        {
                            "timestamp": datetime.now(UTC)
                            .isoformat(timespec="milliseconds")
                            .replace("+00:00", "Z"),
                            "level": "ERROR",
                            "message": f"Logging critical failure: {str(inner_e)}",
                        }
                    )
                except Exception:
                    return "Logging critical failure"


def setup_logging():
    """Configure Python logging centrally."""
    root_logger = logging.getLogger()
    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJSONFormatter())
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Propagate Uvicorn and FastAPI logs to the root logger to format them in JSON
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True


# Initialize logger named "itpa"
logger = logging.getLogger("itpa")
