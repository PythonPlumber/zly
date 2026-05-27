from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
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


async def get_invite_email_data(
    db: AsyncSession,
    invite: Invite,
    base_url: str,
) -> dict | None:
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == invite.invited_by_user_id))
    inviter = result.scalar_one_or_none()
    if not inviter:
        return None
    ws_result = await db.execute(select(Workspace).where(Workspace.id == invite.workspace_id))
    ws = ws_result.scalar_one_or_none()
    if not ws:
        return None
    return {
        "invite_id": invite.id,
        "to_email": invite.email,
        "workspace_name": ws.name,
        "invited_by_name": inviter.display_name or inviter.email,
        "invite_url": f"{base_url}/invites/{invite.token}",
        "expires_at": invite.expires_at.strftime("%Y-%m-%d %H:%M UTC"),
    }


async def accept_invite(db: AsyncSession, token: str, current_user: User | None = None) -> WorkspaceMember | None:
    result = await db.execute(select(Invite).where(Invite.token == token, Invite.status == "pending"))
    invite = result.scalar_one_or_none()
    if not invite:
        return None
    if invite.expires_at < _utcnow():
        invite.status = "expired"
        await db.flush()
        return None
    if current_user and current_user.email != invite.email:
        ws = await db.execute(select(Workspace).where(Workspace.id == invite.workspace_id))
        workspace = ws.scalar_one_or_none()
        if not workspace or workspace.owner_id != current_user.id:
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


async def decline_invite(db: AsyncSession, token: str, current_user: User | None = None) -> bool:
    result = await db.execute(select(Invite).where(Invite.token == token, Invite.status == "pending"))
    invite = result.scalar_one_or_none()
    if not invite:
        return False
    if current_user and current_user.email != invite.email:
        return False
    invite.status = "declined"
    await db.flush()
    return True


async def list_invites(db: AsyncSession, workspace_id: str, page: int = 1, page_size: int = 50) -> tuple[list[Invite], int, bool]:
    base = select(Invite).where(Invite.workspace_id == workspace_id).order_by(Invite.created_at.desc())
    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    invites = list(result.scalars().all())
    has_next = (offset + page_size) < total
    return invites, total, has_next


async def cancel_invite(db: AsyncSession, invite_id: str) -> Invite | None:
    result = await db.execute(select(Invite).where(Invite.id == invite_id))
    invite = result.scalar_one_or_none()
    if not invite:
        return None
    invite.status = "cancelled"
    await db.flush()
    return invite


async def list_members(db: AsyncSession, workspace_id: str, page: int = 1, page_size: int = 50) -> tuple[list[WorkspaceMember], int, bool]:
    base = select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id).order_by(WorkspaceMember.joined_at)
    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    members = list(result.scalars().all())
    has_next = (offset + page_size) < total
    return members, total, has_next


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
