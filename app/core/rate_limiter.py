import asyncio
import logging
import time
from typing import Any

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.logging import get_logger

logger = get_logger(__name__)

ZONES: dict[str, dict[str, Any]] = {}
_IN_MEMORY_BUCKETS: dict[str, list[float]] = {}
_IN_MEMORY_LOCK = asyncio.Lock()
_MAX_BUCKET_KEYS = 10000


def _cleanup_stale_buckets():
    now = time.time()
    stale = []
    for key, timestamps in list(_IN_MEMORY_BUCKETS.items()):
        ts = [t for t in timestamps if t > now - 3600]
        if ts:
            _IN_MEMORY_BUCKETS[key] = ts
        else:
            stale.append(key)
    for k in stale:
        _IN_MEMORY_BUCKETS.pop(k, None)


async def _memory_check(key: str, zone: str) -> tuple[bool, int, int]:
    async with _IN_MEMORY_LOCK:
        now = time.time()
        cfg = ZONES[zone]
        cutoff = now - cfg["window"]
        if len(_IN_MEMORY_BUCKETS) > _MAX_BUCKET_KEYS:
            _cleanup_stale_buckets()
        bucket = _IN_MEMORY_BUCKETS.get(key, [])
        bucket = [t for t in bucket if t > cutoff]
        if len(bucket) >= cfg["max"]:
            retry_after = int(cfg["window"] - (now - bucket[0]))
            return False, max(1, retry_after), 0
        bucket.append(now)
        _IN_MEMORY_BUCKETS[key] = bucket
        remaining = cfg["max"] - len(bucket)
        return True, 0, remaining


def setup_rate_limiter(
    app: FastAPI,
    redirect_requests: int = 100,
    redirect_window: int = 60,
    api_requests: int = 60,
    api_window: int = 60,
    auth_requests: int = 10,
    auth_window: int = 60,
    tracking_requests: int = 60,
    tracking_window: int = 60,
) -> None:
    ZONES["redirect"] = {"max": redirect_requests, "window": redirect_window}
    ZONES["api"] = {"max": api_requests, "window": api_window}
    ZONES["auth"] = {"max": auth_requests, "window": auth_window}
    ZONES["tracking"] = {"max": tracking_requests, "window": tracking_window}

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
        zone = _get_zone(request.url.path)
        if zone is None or zone not in ZONES:
            return await call_next(request)

        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or (request.client.host if request.client else "unknown")
        )
        auth_header = request.headers.get("Authorization", "")
        api_key_prefix = ""
        if auth_header.startswith("Bearer ") and auth_header[7:].startswith("uf_"):
            api_key_prefix = auth_header[7:12]
        key = f"rl:{zone}:{client_ip}:{api_key_prefix}"

        allowed, retry_after, remaining = await _check_rate_limit(key, zone)
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
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + ZONES[zone]["window"])
        return response


async def _check_rate_limit(key: str, zone: str) -> tuple[bool, int, int]:
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
        remaining = ZONES[zone]["max"] - count - 1
        if count >= ZONES[zone]["max"]:
            retry_after = int(ZONES[zone]["window"] - (now - cutoff))
            return False, max(1, retry_after), 0
        return True, 0, max(0, remaining)
    except Exception:
        logger.warning("Redis rate limiter unavailable, falling back to in-memory", extra={"zone": zone})
        return await _memory_check(key, zone)


def _get_zone(path: str) -> str | None:
    if path.startswith("/api/v1/auth/"):
        return "auth"
    if path.startswith("/api/v1/"):
        return "api"
    if path.startswith("/track/") or path.startswith("/l/track/"):
        return "tracking"
    if len(path) > 1 and "/" not in path.strip("/") and path != "/health" and not path.startswith("/dashboard"):
        return "redirect"
    return None