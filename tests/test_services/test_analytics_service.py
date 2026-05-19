import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.click import Click
from app.models.link import Link
from app.schemas.link import LinkCreate
from app.services.analytics_service import (
    get_browser_stats,
    get_clicks_over_time,
    get_device_stats,
    get_os_stats,
    get_top_referrers,
    get_total_clicks,
    get_workspace_summary,
)
from app.services.link_service import create_link


@pytest.mark.asyncio
async def test_total_clicks_empty(db_session: AsyncSession, test_workspace_id: str):
    link = await create_link(db_session, LinkCreate(destination_url="https://example.com", workspace_id=test_workspace_id))
    count = await get_total_clicks(db_session, link.id)
    assert count == 0


@pytest.mark.asyncio
async def test_total_clicks_with_data(db_session: AsyncSession, test_workspace_id: str, test_user_id: str):
    link = await create_link(db_session, LinkCreate(destination_url="https://example.com", workspace_id=test_workspace_id))
    for _ in range(3):
        click = Click(link_id=link.id, ip_hash="abc", browser="Chrome", os="Windows", device_type="desktop")
        db_session.add(click)
    await db_session.flush()
    count = await get_total_clicks(db_session, link.id)
    assert count == 3


@pytest.mark.asyncio
async def test_browser_stats(db_session: AsyncSession, test_workspace_id: str, test_user_id: str):
    link = await create_link(db_session, LinkCreate(destination_url="https://example.com", workspace_id=test_workspace_id))
    for browser in ["Chrome", "Chrome", "Firefox"]:
        db_session.add(Click(link_id=link.id, ip_hash="abc", browser=browser))
    await db_session.flush()
    stats = await get_browser_stats(db_session, link.id)
    assert len(stats) == 2
    assert stats[0]["browser"] == "Chrome"
    assert stats[0]["count"] == 2


@pytest.mark.asyncio
async def test_device_stats(db_session: AsyncSession, test_workspace_id: str, test_user_id: str):
    link = await create_link(db_session, LinkCreate(destination_url="https://example.com", workspace_id=test_workspace_id))
    for device in ["mobile", "mobile", "desktop"]:
        db_session.add(Click(link_id=link.id, ip_hash="abc", device_type=device))
    await db_session.flush()
    stats = await get_device_stats(db_session, link.id)
    assert len(stats) == 2


@pytest.mark.asyncio
async def test_os_stats(db_session: AsyncSession, test_workspace_id: str, test_user_id: str):
    link = await create_link(db_session, LinkCreate(destination_url="https://example.com", workspace_id=test_workspace_id))
    db_session.add(Click(link_id=link.id, ip_hash="abc", os="Windows"))
    db_session.add(Click(link_id=link.id, ip_hash="def", os="macOS"))
    await db_session.flush()
    stats = await get_os_stats(db_session, link.id)
    assert len(stats) == 2


@pytest.mark.asyncio
async def test_top_referrers(db_session: AsyncSession, test_workspace_id: str, test_user_id: str):
    link = await create_link(db_session, LinkCreate(destination_url="https://example.com", workspace_id=test_workspace_id))
    for _ in range(3):
        db_session.add(Click(link_id=link.id, ip_hash="abc", referrer_domain="google.com"))
    db_session.add(Click(link_id=link.id, ip_hash="def", referrer_domain="twitter.com"))
    await db_session.flush()
    refs = await get_top_referrers(db_session, link.id)
    assert len(refs) == 2
    assert refs[0]["domain"] == "google.com"
    assert refs[0]["count"] == 3


@pytest.mark.asyncio
async def test_workspace_summary(db_session: AsyncSession, test_workspace_id: str, test_user_id: str):
    link1 = await create_link(db_session, LinkCreate(destination_url="https://a.com", workspace_id=test_workspace_id))
    link2 = await create_link(db_session, LinkCreate(destination_url="https://b.com", workspace_id=test_workspace_id))
    for _ in range(2):
        db_session.add(Click(link_id=link1.id, ip_hash="abc"))
    db_session.add(Click(link_id=link2.id, ip_hash="def"))
    await db_session.flush()
    summary = await get_workspace_summary(db_session, test_workspace_id)
    assert summary["total_clicks"] == 3
    assert summary["total_links"] == 2
