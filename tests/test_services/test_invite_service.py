import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Invite, WorkspaceMember
from app.services.invite_service import (
    accept_invite,
    cancel_invite,
    create_invite,
    decline_invite,
    list_invites,
    list_members,
    remove_member,
)
from app.services.workspace_service import create_workspace
from app.schemas.workspace import WorkspaceCreate


@pytest.mark.asyncio
async def test_create_invite(db_session: AsyncSession, test_user_id: str):
    ws = await create_workspace(db_session, WorkspaceCreate(name="Invite WS", slug="invite-ws"), test_user_id)
    invite = await create_invite(db_session, ws.id, test_user_id, "test@example.com", "member")
    assert invite.email == "test@example.com"
    assert invite.status == "pending"
    assert invite.token is not None


@pytest.mark.asyncio
async def test_accept_invite(db_session: AsyncSession, test_user_id: str):
    ws = await create_workspace(db_session, WorkspaceCreate(name="Accept WS", slug="accept-ws"), test_user_id)
    invite = await create_invite(db_session, ws.id, test_user_id, "accept@test.com", "member")
    member = await accept_invite(db_session, invite.token)
    assert member is None  # no user with that email exists


@pytest.mark.asyncio
async def test_accept_invite_with_user(db_session: AsyncSession, test_user_id: str):
    from app.core.security import hash_password
    from app.models.user import User

    user = User(email="accept2@test.com", password_hash=hash_password("pass"), display_name="Accept")
    db_session.add(user)
    await db_session.flush()

    ws = await create_workspace(db_session, WorkspaceCreate(name="Accept2 WS", slug="accept2-ws"), test_user_id)
    invite = await create_invite(db_session, ws.id, test_user_id, "accept2@test.com", "member")

    member = await accept_invite(db_session, invite.token)
    assert member is not None
    assert member.user_id == user.id
    assert member.role == "member"

    assert invite.status == "accepted"


@pytest.mark.asyncio
async def test_decline_invite(db_session: AsyncSession, test_user_id: str):
    ws = await create_workspace(db_session, WorkspaceCreate(name="Decline WS", slug="decline-ws"), test_user_id)
    invite = await create_invite(db_session, ws.id, test_user_id, "decline@test.com", "member")
    ok = await decline_invite(db_session, invite.token)
    assert ok is True
    assert invite.status == "declined"


@pytest.mark.asyncio
async def test_cancel_invite(db_session: AsyncSession, test_user_id: str):
    ws = await create_workspace(db_session, WorkspaceCreate(name="Cancel WS", slug="cancel-ws"), test_user_id)
    invite = await create_invite(db_session, ws.id, test_user_id, "cancel@test.com", "member")
    cancelled = await cancel_invite(db_session, invite.id)
    assert cancelled is not None
    assert cancelled.status == "cancelled"


@pytest.mark.asyncio
async def test_list_members(db_session: AsyncSession, test_user_id: str):
    ws = await create_workspace(db_session, WorkspaceCreate(name="Members WS", slug="members-ws"), test_user_id)
    members = await list_members(db_session, ws.id)
    assert len(members) == 1
    assert members[0].user_id == test_user_id
    assert members[0].role == "owner"


@pytest.mark.asyncio
async def test_remove_member(db_session: AsyncSession, test_user_id: str):
    from app.core.security import hash_password
    from app.models.user import User

    user = User(email="remove@test.com", password_hash=hash_password("pass"), display_name="Remove")
    db_session.add(user)
    await db_session.flush()

    ws = await create_workspace(db_session, WorkspaceCreate(name="Remove WS", slug="remove-ws"), test_user_id)
    db_session.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="member"))
    await db_session.flush()

    ok = await remove_member(db_session, ws.id, user.id)
    assert ok is True

    members = await list_members(db_session, ws.id)
    assert len(members) == 1
