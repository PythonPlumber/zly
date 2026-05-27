import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.router import api_router, redirect_router
from app.api.email_tracking import router as email_tracking_router
from app.routes.auth_routes import router as auth_router
from app.config import settings
from app.core.rate_limiter import setup_rate_limiter
from app.core.csrf import CSRFMiddleware
from app.core.request_id import RequestIDMiddleware
from app.core.logging import setup_logging, get_logger
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.redis import close_redis, get_redis
from app.routes.dashboard import router as dashboard_router
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)

START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = get_logger(__name__)

    try:
        from app.db import get_session_factory
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception as e:
        logger.critical("Database unreachable on startup", extra={"error": str(e)})
        raise

    try:
        redis = await get_redis()
        await redis.ping()
        logger.info("Redis connection verified")
    except Exception:
        logger.warning("Redis unreachable on startup — some features degraded")

    is_prod = os.getenv("ENVIRONMENT", "").lower() in ("production", "prod")
    default_warnings = []
    if settings.secret_key == "change-me-in-production":
        default_warnings.append("SECRET_KEY")
    if settings.jwt_secret == "change-me-in-production":
        default_warnings.append("JWT_SECRET")
    if default_warnings:
        msg = f"Default secrets in use: {', '.join(default_warnings)}. Set strong values in production."
        if is_prod:
            logger.critical(msg)
            raise RuntimeError(msg)
        logger.warning(msg)

    yield
    await close_redis()


app = FastAPI(
    title="Zly API",
    description="Open-source URL shortener and marketing platform. Shorten URLs, track clicks, manage campaigns, and more.",
    version="0.1.0",
    contact={
        "name": "PythonPlumber",
        "url": "https://senuka.me",
        "email": "pythonplumber@senuka.me",
    },
    license_info={
        "name": "MIT",
        "url": "https://github.com/pythonplumber/zly/blob/main/LICENSE",
    },
    lifespan=lifespan,
    openapi_tags=[
        {"name": "auth", "description": "Authentication and user registration"},
        {"name": "links", "description": "Create, update, delete, and manage short links"},
        {"name": "workspaces", "description": "Workspace management"},
        {"name": "tags", "description": "Organize links with tags"},
        {"name": "webhooks", "description": "Webhook integrations for events"},
        {"name": "api-keys", "description": "API key management for programmatic access"},
        {"name": "analytics", "description": "Click analytics and statistics"},
        {"name": "domains", "description": "Custom domain management"},
        {"name": "invites", "description": "Workspace member invites"},
        {"name": "bio", "description": "Link-in-bio pages"},
        {"name": "ab-testing", "description": "A/B testing variants for links"},
        {"name": "bulk", "description": "Bulk import and export operations"},
        {"name": "email-campaigns", "description": "Email campaign management"},
        {"name": "email-tracking", "description": "Email open and click tracking"},
        {"name": "audit", "description": "Audit log access"},
        {"name": "admin", "description": "Superuser admin operations"},
        {"name": "oauth", "description": "OAuth/SSO login with Google and GitHub"},
        {"name": "users", "description": "User profile and settings"},
        {"name": "sessions", "description": "Session management and revocation"},
    ],
)

sentry_dsn = os.getenv("SENTRY_DSN", "")
if sentry_dsn:
    import sentry_sdk
    sentry_sdk.init(dsn=sentry_dsn, traces_sample_rate=0.1)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware)

if settings.rate_limit_enabled:
    setup_rate_limiter(
        app,
        redirect_requests=settings.rate_limit_redirect,
        redirect_window=settings.rate_limit_window,
        api_requests=settings.rate_limit_api,
        api_window=settings.rate_limit_window,
        auth_requests=settings.rate_limit_auth,
        auth_window=settings.rate_limit_window,
        tracking_requests=settings.rate_limit_tracking,
        tracking_window=settings.rate_limit_window,
    )

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(api_router, prefix="/api/v1")
app.include_router(email_tracking_router)


@app.get("/health")
async def health():
    db_ok = "unknown"
    redis_ok = "unknown"

    try:
        from app.db import get_session_factory
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(text("SELECT 1"))
        db_ok = "ok"
    except Exception:
        db_ok = "error"

    try:
        redis = await get_redis()
        await redis.ping()
        redis_ok = "ok"
    except Exception:
        redis_ok = "error"

    return {
        "status": "ok",
        "database": db_ok,
        "redis": redis_ok,
        "version": "0.1.0",
        "uptime_seconds": int(time.time() - START_TIME),
    }


app.include_router(redirect_router)
