import logging
import time
from typing import Any

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.logging import get_logger

logger = get_logger(__name__)

ZONES: dict[str, dict[str, Any]] = {}


def setup_rate_limiter(
    app: FastAPI,
    redirect_requests: int = 100,
    redirect_window: int = 60,
    api_requests: int = 60,
    api_window: int = 60,
    auth_requests: int = 10,
    auth_window: int = 60,
) -> None:
    ZONES["redirect"] = {"max": redirect_requests, "window": redirect_window}
    ZONES["api"] = {"max": api_requests, "window": api_window}
    ZONES["auth"] = {"max": auth_requests, "window": auth_window}

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
        zone = _get_zone(request.url.path)
        if zone is None or zone not in ZONES:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"rl:{zone}:{client_ip}"

        allowed, retry_after = await _check_rate_limit(key, zone)
        if not allowed:
            return Response(
                status_code=429,
                content='{"error":"Too Many Requests","detail":"Rate limit exceeded. Please wait and retry."}',
                media_type="application/json",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(ZONES[zone]["max"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(ZONES[zone]["max"])
        response.headers["X-RateLimit-Remaining"] = str(ZONES[zone]["max"] - 1)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + ZONES[zone]["window"])
        return response


async def _check_rate_limit(key: str, zone: str) -> tuple[bool, int]:
    try:
        from app.core.redis import get_redis

        redis_client = await get_redis()
        now = time.time()
        cutoff = now - ZONES[zone]["window"]
        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, cutoff)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, ZONES[zone]["window"])
        results = await pipe.execute()
        count = results[1]
        if count >= ZONES[zone]["max"]:
            retry_after = int(ZONES[zone]["window"] - (now - cutoff))
            return False, max(1, retry_after)
        return True, 0
    except Exception:
        logger.warning("Redis rate limiter unavailable, allowing request", extra={"zone": zone})
        return True, 0


def _get_zone(path: str) -> str | None:
    if path.startswith("/api/v1/auth/"):
        return "auth"
    if path.startswith("/api/v1/"):
        return "api"
    if len(path) > 1 and "/" not in path.strip("/") and path != "/health" and not path.startswith("/dashboard"):
        return "redirect"
    return None