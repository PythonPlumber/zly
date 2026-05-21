import logging
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from app.core.request_id import get_request_id

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": get_request_id(),
        },
        headers={"X-Request-ID": get_request_id()} if get_request_id() else None,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    def _simplify_error(err: dict) -> dict:
        result = {}
        for k, v in err.items():
            if isinstance(v, dict):
                result[k] = _simplify_error(v)
            elif isinstance(v, list):
                result[k] = [_simplify_error(i) if isinstance(i, dict) else str(i) for i in v]
            elif hasattr(v, "__class__") and "ValidationError" in v.__class__.__name__:
                result[k] = str(v)
            else:
                try:
                    import json as _json
                    _json.dumps(v)
                    result[k] = v
                except (TypeError, ValueError):
                    result[k] = str(v)
        return result

    simplified = [_simplify_error(e) for e in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={
            "detail": simplified,
            "request_id": get_request_id(),
        },
        headers={"X-Request-ID": get_request_id()} if get_request_id() else None,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception", exc_info=exc, extra={
        "path": str(request.url.path),
        "method": request.method,
    })
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "request_id": get_request_id(),
        },
        headers={"X-Request-ID": get_request_id()} if get_request_id() else None,
    )