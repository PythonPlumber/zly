import json
import logging
import pytest
from io import StringIO

from app.core.request_id import request_id_var


@pytest.fixture(autouse=True)
def reset_logging():
    root = logging.getLogger()
    old_handlers = root.handlers.copy()
    old_level = root.level
    root.handlers.clear()
    yield
    root.handlers = old_handlers
    root.level = old_level


def test_json_formatter_output():
    from app.core.logging import JSONFormatter

    handler = logging.StreamHandler(StringIO())
    handler.setFormatter(JSONFormatter())
    logger = logging.getLogger("test_logger")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    logger.info("hello", extra={"request_id": "abc-123"})

    output = handler.stream.getvalue()
    parsed = json.loads(output)
    assert parsed["msg"] == "hello"
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert parsed["request_id"] == "abc-123"


def test_get_logger_injects_request_id():
    from app.core.logging import get_logger, JSONFormatter
    import app.core.request_id as req_id_mod

    req_id_mod.request_id_var.set("test-req-456")

    handler = logging.StreamHandler(StringIO())
    handler.setFormatter(JSONFormatter())
    logger = get_logger("test_inject")
    logger.logger.addHandler(handler)
    logger.logger.setLevel(logging.INFO)

    logger.info("test message")

    output = handler.stream.getvalue()
    parsed = json.loads(output)
    assert parsed["request_id"] == "test-req-456"