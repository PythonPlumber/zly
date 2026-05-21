import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.router import api_router, redirect_router
from app.core.rate_limiter import setup_rate_limiter, ZONES
from app.core.dependencies import get_db, get_redis_client
from app.routes.dashboard import router as dashboard_router


@pytest_asyncio.fixture
async def rate_limited_client(db_session: AsyncSession, mock_redis):
    ZONES.clear()
    test_app = FastAPI()
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    setup_rate_limiter(test_app)
    test_app.include_router(dashboard_router)
    test_app.include_router(api_router, prefix="/api/v1")

    @test_app.get("/health")
    async def health():
        return {"status": "ok"}

    test_app.include_router(redirect_router)

    async def override_get_db():
        yield db_session

    async def override_redis():
        yield mock_redis

    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_redis_client] = override_redis
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_rate_limit_auth_block(rate_limited_client: AsyncClient):
    for _ in range(12):
        r = await rate_limited_client.post(
            "/api/v1/auth/login",
            json={"email": "x@x.com", "password": "x"},
        )
    assert r.status_code == 429


@pytest.mark.asyncio
async def test_rate_limit_auth_allowed(rate_limited_client: AsyncClient):
    r = await rate_limited_client.post(
        "/api/v1/auth/login",
        json={"email": "x@x.com", "password": "x"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_health_not_rate_limited(rate_limited_client: AsyncClient):
    for _ in range(200):
        r = await rate_limited_client.get("/health")
    assert r.status_code == 200
