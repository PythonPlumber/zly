import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.logging import get_logger
logger = get_logger(__name__)


class SlidingWindowCounter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> tuple[bool, int]:
        now = time.time()
        cutoff = now - self.window_seconds
        bucket = self._buckets[key]
        while bucket and bucket[0] < cutoff:
            bucket.pop(0)
        if len(bucket) >= self.max_requests:
            retry_after = int(bucket[0] + self.window_seconds - now) + 1
            return False, retry_after
        bucket.append(now)
        return True, 0


ZONES: dict[str, SlidingWindowCounter] = {}


def setup_rate_limiter(
    app: FastAPI,
    redirect_requests: int = 100,
    redirect_window: int = 60,
    api_requests: int = 60,
    api_window: int = 60,
    auth_requests: int = 10,
    auth_window: int = 60,
) -> None:
    ZONES["redirect"] = SlidingWindowCounter(redirect_requests, redirect_window)
    ZONES["api"] = SlidingWindowCounter(api_requests, api_window)
    ZONES["auth"] = SlidingWindowCounter(auth_requests, auth_window)

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
        zone = _get_zone(request.url.path)
        if zone is None or zone not in ZONES:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"{zone}:{client_ip}"
        counter = ZONES[zone]
        allowed, retry_after = counter.allow(key)
        if not allowed:
            logger.warning("Rate limit exceeded", extra={"zone": zone, "key": key, "retry_after": retry_after})
            return Response(
                status_code=429,
                content='{"error":"Too Many Requests","detail":"Rate limit exceeded. Please wait and retry."}',
                media_type="application/json",
                headers={"Retry-After": str(retry_after), "X-RateLimit-Reset": str(int(time.time()) + retry_after)},
            )
        return await call_next(request)


def _get_zone(path: str) -> str | None:
    if path.startswith("/api/v1/auth/"):
        return "auth"
    if path.startswith("/api/v1/"):
        return "api"
    if len(path) > 1 and "/" not in path.strip("/") and path != "/health" and not path.startswith("/dashboard"):
        return "redirect"
    return None
