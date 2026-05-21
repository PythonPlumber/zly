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
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": get_request_id(),
        },
        headers={"X-Request-ID": get_request_id()} if get_request_id() else None,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
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