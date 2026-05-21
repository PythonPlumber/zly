import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.core.dependencies import get_db, get_redis_client
from app.db import Base
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_zly.db"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def mock_redis():
    mock = AsyncMock()
    mock.get.return_value = None
    return mock


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, mock_redis) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    async def override_redis():
        yield mock_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_client] = override_redis
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user_id(db_session: AsyncSession) -> str:
    from app.core.security import hash_password
    from app.models.user import User

    user = User(
        email="testuser@test.com",
        password_hash=hash_password("testpass"),
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user.id


@pytest_asyncio.fixture
async def test_workspace_id(db_session: AsyncSession, test_user_id: str) -> str:
    from app.schemas.workspace import WorkspaceCreate
    from app.services.workspace_service import create_workspace

    ws = await create_workspace(
        db_session, WorkspaceCreate(name="Global Test WS", slug="global-test-ws"), test_user_id
    )
    return ws.id


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient, db_session: AsyncSession) -> AsyncClient:
    from app.schemas.auth import RegisterRequest
    from app.services.auth_service import register_user

    user = await register_user(
        db_session,
        RegisterRequest(email="authuser@test.com", password="testpass123"),
    )
    from app.core.security import create_access_token

    token = create_access_token({"sub": user.id})
    client.headers["Authorization"] = f"Bearer {token}"
    return client
