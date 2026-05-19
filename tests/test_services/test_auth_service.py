import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.models.workspace import Workspace
from app.schemas.auth import RegisterRequest
from app.services.auth_service import register_user, authenticate_user


@pytest.mark.asyncio
async def test_register_user(db_session: AsyncSession):
    user = await register_user(
        db_session,
        RegisterRequest(email="new@test.com", password="secret123", display_name="New User"),
    )
    assert user.email == "new@test.com"
    assert user.display_name == "New User"
    assert user.password_hash != "secret123"


@pytest.mark.asyncio
async def test_register_duplicate_email(db_session: AsyncSession):
    await register_user(db_session, RegisterRequest(email="dup@test.com", password="secret123"))
    with pytest.raises(ValueError, match="Email already registered"):
        await register_user(db_session, RegisterRequest(email="dup@test.com", password="secret456"))


@pytest.mark.asyncio
async def test_authenticate_user(db_session: AsyncSession):
    await register_user(db_session, RegisterRequest(email="auth@test.com", password="secret123"))
    user = await authenticate_user(db_session, "auth@test.com", "secret123")
    assert user is not None
    assert user.email == "auth@test.com"


@pytest.mark.asyncio
async def test_register_creates_personal_workspace(db_session: AsyncSession):
    user = await register_user(
        db_session,
        RegisterRequest(email="wsauto@test.com", password="secret123"),
    )
    result = await db_session.execute(
        select(Workspace).where(Workspace.owner_id == user.id)
    )
    ws = result.scalar_one_or_none()
    assert ws is not None
    assert ws.owner_id == user.id


@pytest.mark.asyncio
async def test_authenticate_wrong_password(db_session: AsyncSession):
    await register_user(db_session, RegisterRequest(email="wrong@test.com", password="secret123"))
    user = await authenticate_user(db_session, "wrong@test.com", "wrongpass")
    assert user is None
