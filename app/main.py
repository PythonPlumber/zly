from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router, redirect_router
from app.routes.auth_routes import router as auth_router
from app.config import settings
from app.core.rate_limiter import setup_rate_limiter
from app.core.csrf import CSRFMiddleware
from app.core.request_id import RequestIDMiddleware
from app.core.logging import setup_logging
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.redis import close_redis
from app.routes.dashboard import router as dashboard_router
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield
    await close_redis()


app = FastAPI(title="Zly", version="0.1.0", lifespan=lifespan)

import os
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
    )

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(redirect_router)
