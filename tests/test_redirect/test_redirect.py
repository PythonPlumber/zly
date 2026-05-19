import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link


@pytest.mark.asyncio
async def test_redirect_basic(client: AsyncClient, db_session: AsyncSession, test_workspace_id: str):
    link = Link(short_code="test123", destination_url="https://example.com", workspace_id=test_workspace_id)
    db_session.add(link)
    await db_session.flush()

    response = await client.get("/test123", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com"


@pytest.mark.asyncio
async def test_redirect_not_found(client: AsyncClient):
    response = await client.get("/nonexist", follow_redirects=False)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_redirect_inactive_link(client: AsyncClient, db_session: AsyncSession, test_workspace_id: str):
    link = Link(short_code="inactive", destination_url="https://example.com", is_active=False, workspace_id=test_workspace_id)
    db_session.add(link)
    await db_session.flush()

    response = await client.get("/inactive", follow_redirects=False)
    assert response.status_code == 410


@pytest.mark.asyncio
async def test_redirect_expired_link(client: AsyncClient, db_session: AsyncSession, test_workspace_id: str):
    from datetime import datetime, timedelta, timezone
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    link = Link(short_code="expired", destination_url="https://example.com", expires_at=past, workspace_id=test_workspace_id)
    db_session.add(link)
    await db_session.flush()

    response = await client.get("/expired", follow_redirects=False)
    assert response.status_code == 410


@pytest.mark.asyncio
async def test_redirect_not_yet_active(client: AsyncClient, db_session: AsyncSession, test_workspace_id: str):
    from datetime import datetime, timedelta, timezone
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    link = Link(short_code="future", destination_url="https://example.com", activate_at=future, workspace_id=test_workspace_id)
    db_session.add(link)
    await db_session.flush()

    response = await client.get("/future", follow_redirects=False)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_redirect_password_protected(client: AsyncClient, db_session: AsyncSession, test_workspace_id: str):
    from app.core.security import hash_password
    link = Link(short_code="secret", destination_url="https://secret.com", password_hash=hash_password("hunter2"), workspace_id=test_workspace_id)
    db_session.add(link)
    await db_session.flush()

    response = await client.get("/secret", follow_redirects=False)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_redirect_password_protected_correct(client: AsyncClient, db_session: AsyncSession, test_workspace_id: str):
    from app.core.security import hash_password
    link = Link(short_code="secret2", destination_url="https://secret.com", password_hash=hash_password("hunter2"), workspace_id=test_workspace_id)
    db_session.add(link)
    await db_session.flush()

    response = await client.get("/secret2?password=hunter2", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://secret.com"


@pytest.mark.asyncio
async def test_redirect_password_protected_wrong(client: AsyncClient, db_session: AsyncSession, test_workspace_id: str):
    from app.core.security import hash_password
    link = Link(short_code="secret3", destination_url="https://secret.com", password_hash=hash_password("hunter2"), workspace_id=test_workspace_id)
    db_session.add(link)
    await db_session.flush()

    response = await client.get("/secret3?password=wrong", follow_redirects=False)
    assert response.status_code == 403
