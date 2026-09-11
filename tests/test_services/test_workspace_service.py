import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.workspace import WorkspaceCreate
from app.services.workspace_service import create_workspace, get_workspace, get_workspaces_for_user


@pytest.mark.asyncio
async def test_create_workspace(db_session: AsyncSession):
    user = User(email="ws@test.com", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    ws = await create_workspace(
        db_session,
        WorkspaceCreate(name="My Team", slug="my-team"),
        user.id,
    )
    assert ws.name == "My Team"
    assert ws.slug == "my-team"
    assert ws.owner_id == user.id


@pytest.mark.asyncio
async def test_get_workspaces_for_user(db_session: AsyncSession):
    user = User(email="list@test.com", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    await create_workspace(db_session, WorkspaceCreate(name="WS 1"), user.id)
    await create_workspace(db_session, WorkspaceCreate(name="WS 2"), user.id)
    workspaces, _, _ = await get_workspaces_for_user(db_session, user.id)
    assert len(workspaces) == 2


@pytest.mark.asyncio
async def test_get_workspace(db_session: AsyncSession):
    user = User(email="get@test.com", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    ws = await create_workspace(db_session, WorkspaceCreate(name="Get Me"), user.id)
    fetched = await get_workspace(db_session, ws.id)
    assert fetched is not None
    assert fetched.name == "Get Me"


@pytest.mark.asyncio
async def test_get_workspace_not_found(db_session: AsyncSession):
    fetched = await get_workspace(db_session, "nonexistent-id")
    assert fetched is None
