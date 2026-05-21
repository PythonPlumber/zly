from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import secrets
from app.models.user import User
from app.models.workspace import Invite, Workspace, WorkspaceMember


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def create_invite(
    db: AsyncSession, workspace_id: str, invited_by_user_id: str, email: str, role: str
) -> Invite:
    token = secrets.token_urlsafe(48)
    expires_at = _utcnow() + timedelta(days=7)
    invite = Invite(
        workspace_id=workspace_id,
        invited_by_user_id=invited_by_user_id,
        email=email,
        role=role,
        token=token,
        expires_at=expires_at,
    )
    db.add(invite)
    await db.flush()
    await db.refresh(invite)
    return invite


async def accept_invite(db: AsyncSession, token: str) -> WorkspaceMember | None:
    result = await db.execute(select(Invite).where(Invite.token == token, Invite.status == "pending"))
    invite = result.scalar_one_or_none()
    if not invite:
        return None
    if invite.expires_at < _utcnow():
        invite.status = "expired"
        await db.flush()
        return None
    user_result = await db.execute(select(User).where(User.email == invite.email))
    user = user_result.scalar_one_or_none()
    if not user:
        return None
    member = WorkspaceMember(
        workspace_id=invite.workspace_id,
        user_id=user.id,
        role=invite.role,
    )
    db.add(member)
    invite.status = "accepted"
    await db.flush()
    await db.refresh(member)
    return member


async def decline_invite(db: AsyncSession, token: str) -> bool:
    result = await db.execute(select(Invite).where(Invite.token == token, Invite.status == "pending"))
    invite = result.scalar_one_or_none()
    if not invite:
        return False
    invite.status = "declined"
    await db.flush()
    return True


async def list_invites(db: AsyncSession, workspace_id: str) -> list[Invite]:
    result = await db.execute(
        select(Invite)
        .where(Invite.workspace_id == workspace_id)
        .order_by(Invite.created_at.desc())
    )
    return list(result.scalars().all())


async def cancel_invite(db: AsyncSession, invite_id: str) -> Invite | None:
    result = await db.execute(select(Invite).where(Invite.id == invite_id))
    invite = result.scalar_one_or_none()
    if not invite:
        return None
    invite.status = "cancelled"
    await db.flush()
    return invite


async def list_members(db: AsyncSession, workspace_id: str) -> list[WorkspaceMember]:
    result = await db.execute(
        select(WorkspaceMember)
        .where(WorkspaceMember.workspace_id == workspace_id)
        .order_by(WorkspaceMember.joined_at)
    )
    return list(result.scalars().all())


async def remove_member(db: AsyncSession, workspace_id: str, user_id: str) -> bool:
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        return False
    await db.delete(member)
    await db.flush()
    return True
