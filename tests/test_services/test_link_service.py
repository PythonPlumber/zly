import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.link import LinkCreate
from app.services.link_service import create_link, get_link_by_code, get_links


@pytest.mark.asyncio
async def test_create_link(db_session: AsyncSession, test_workspace_id: str):
    data = LinkCreate(destination_url="https://example.com", title="My Link", workspace_id=test_workspace_id)
    link = await create_link(db_session, data)
    assert link.destination_url == "https://example.com"
    assert link.title == "My Link"
    assert len(link.short_code) == 7
    assert link.is_active is True


@pytest.mark.asyncio
async def test_create_link_custom_code(db_session: AsyncSession, test_workspace_id: str):
    data = LinkCreate(destination_url="https://example.com", short_code="custom1", workspace_id=test_workspace_id)
    link = await create_link(db_session, data)
    assert link.short_code == "custom1"


@pytest.mark.asyncio
async def test_get_link_by_code(db_session: AsyncSession, test_workspace_id: str):
    data = LinkCreate(destination_url="https://example.com", workspace_id=test_workspace_id)
    created = await create_link(db_session, data)
    fetched = await get_link_by_code(db_session, created.short_code)
    assert fetched is not None
    assert fetched.id == created.id


@pytest.mark.asyncio
async def test_get_link_by_code_not_found(db_session: AsyncSession):
    fetched = await get_link_by_code(db_session, "nonexist")
    assert fetched is None


@pytest.mark.asyncio
async def test_get_links_empty(db_session: AsyncSession, test_workspace_id: str):
    links = await get_links(db_session, workspace_id=test_workspace_id)
    assert links == []


@pytest.mark.asyncio
async def test_get_links_pagination(db_session: AsyncSession, test_workspace_id: str):
    for i in range(5):
        data = LinkCreate(destination_url=f"https://example{i}.com", workspace_id=test_workspace_id)
        await create_link(db_session, data)
    links = await get_links(db_session, workspace_id=test_workspace_id, limit=3)
    assert len(links) == 3


@pytest.mark.asyncio
async def test_create_link_with_password(db_session: AsyncSession, test_workspace_id: str):
    data = LinkCreate(destination_url="https://secret.com", password="hunter2", workspace_id=test_workspace_id)
    link = await create_link(db_session, data)
    assert link.password_hash is not None
    assert link.password_hash != "hunter2"
    from app.core.security import verify_password
    assert verify_password("hunter2", link.password_hash)


@pytest.mark.asyncio
async def test_create_link_with_activate_at(db_session: AsyncSession, test_workspace_id: str):
    from datetime import datetime, timedelta, timezone
    future = datetime.now(timezone.utc) + timedelta(days=7)
    data = LinkCreate(destination_url="https://future.com", activate_at=future, workspace_id=test_workspace_id)
    link = await create_link(db_session, data)
    assert link.activate_at is not None


@pytest.mark.asyncio
async def test_create_link_with_expires_at(db_session: AsyncSession, test_workspace_id: str):
    from datetime import datetime, timedelta, timezone
    future = datetime.now(timezone.utc) + timedelta(days=30)
    data = LinkCreate(destination_url="https://limited.com", expires_at=future, workspace_id=test_workspace_id)
    link = await create_link(db_session, data)
    assert link.expires_at is not None
