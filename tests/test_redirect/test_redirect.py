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
