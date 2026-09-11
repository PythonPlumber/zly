import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "msg": record.getMessage(),
                "request_id": getattr(record, "request_id", None),
                "exc": self.formatException(record.exc_info) if record.exc_info else None,
            },
            default=str,
        )


def setup_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)
    root.setLevel(logging.INFO)


class LoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        from app.core.request_id import get_request_id
        rid = get_request_id()
        if rid:
            kwargs.setdefault("extra", {})["request_id"] = rid
        return msg, kwargs


def get_logger(name: str) -> LoggerAdapter:
    return LoggerAdapter(logging.getLogger(name), {})