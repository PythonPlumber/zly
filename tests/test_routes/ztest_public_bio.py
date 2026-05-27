import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.bio import BioPageCreate, BioLinkCreate
from app.schemas.link import LinkCreate
from app.services.bio_service import create_bio_page, add_bio_link
from app.services.link_service import create_link


@pytest.mark.asyncio
async def test_public_bio_page_renders(client: AsyncClient, db_session: AsyncSession, test_workspace_id: str, test_user_id: str):
    bio = await create_bio_page(
        db_session, test_workspace_id,
        BioPageCreate(slug="test-bio", title="Test Bio Page"),
    )
    link = await create_link(
        db_session,
        LinkCreate(destination_url="https://example.com", workspace_id=test_workspace_id),
        test_user_id,
    )
    await add_bio_link(
        db_session, bio.id,
        BioLinkCreate(title="My Link", url="https://example.com", link_id=link.id),
    )
    r = await client.get("/bio/test-bio")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert "Test Bio Page" in r.text


@pytest.mark.asyncio
async def test_public_bio_page_not_found(client: AsyncClient):
    r = await client.get("/bio/nonexistent-slug")
    assert r.status_code == 404



