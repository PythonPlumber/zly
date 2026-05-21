import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.models.click import Click
from app.models.user import User


@pytest.mark.asyncio
async def test_create_link(db_session: AsyncSession, test_workspace_id: str):
    link = Link(
        short_code="abc1234",
        destination_url="https://example.com",
        title="Test Link",
        workspace_id=test_workspace_id,
    )
    db_session.add(link)
    await db_session.flush()

    result = await db_session.execute(select(Link).where(Link.short_code == "abc1234"))
    fetched = result.scalar_one()
    assert fetched.destination_url == "https://example.com"
    assert fetched.is_active is True
    assert fetched.short_code == "abc1234"


@pytest.mark.asyncio
async def test_create_click(db_session: AsyncSession, test_workspace_id: str):
    link = Link(short_code="clicktest", destination_url="https://example.com", workspace_id=test_workspace_id)
    db_session.add(link)
    await db_session.flush()

    click = Click(
        link_id=link.id,
        ip_hash="abc123hash",
        user_agent="Mozilla/5.0",
    )
    db_session.add(click)
    await db_session.flush()

    result = await db_session.execute(select(Click).where(Click.link_id == link.id))
    fetched = result.scalar_one()
    assert fetched.ip_hash == "abc123hash"


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    user = User(
        email="test@example.com",
        password_hash="hashed_password_here",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.flush()

    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    fetched = result.scalar_one()
    assert fetched.email == "test@example.com"
    assert fetched.display_name == "Test User"
    assert fetched.is_active is True
