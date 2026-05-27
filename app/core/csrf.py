import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_403_FORBIDDEN

from app.core.logging import get_logger
logger = get_logger(__name__)

CSRF_COOKIE_NAME = "zly_csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
SKIP_PREFIXES = {"/api/v1/auth", "/bio", "/health", "/login", "/register"}


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            response: Response = await call_next(request)
            if not request.cookies.get(CSRF_COOKIE_NAME):
                from app.config import settings
                response.set_cookie(
                    key=CSRF_COOKIE_NAME,
                    value=secrets.token_hex(32),
                    httponly=True,
                    secure=settings.secure_cookies,
                    samesite="strict",
                    path="/",
                )
            return response

        if request.headers.get("Authorization", "").startswith("Bearer "):
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(p) for p in SKIP_PREFIXES):
            return await call_next(request)

        if not path.startswith("/api/") and not path.startswith("/dashboard"):
            return await call_next(request)

        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)

        if not cookie_token or not header_token or cookie_token != header_token:
            logger.warning("CSRF validation failed", extra={
                "path": str(request.url.path),
                "method": request.method,
                "has_cookie": bool(cookie_token),
                "has_header": bool(header_token),
            })
            return JSONResponse(
                status_code=HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token missing or invalid"},
            )

        return await call_next(request)
