from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.invite import InviteCreate, InviteResponse, MemberResponse
from app.services.invite_service import (
    accept_invite,
    cancel_invite,
    create_invite,
    decline_invite,
    get_invite_email_data,
    list_invites,
    list_members,
    remove_member,
)
from app.services.workspace_service import verify_workspace_access

logger = get_logger(__name__)

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["invites"])


@router.post("/invites", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def api_create_invite(
    workspace_id: str,
    data: InviteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await verify_workspace_access(db, workspace_id, current_user, require_owner=True)
    invite = await create_invite(db, workspace_id, current_user.id, data.email, data.role)

    email_data = await get_invite_email_data(db, invite, settings.default_domain)
    if email_data:
        try:
            from app.core.arq_pool import get_arq_pool
            pool = await get_arq_pool()
            await pool.enqueue_job("send_invite_email_job", **email_data)
        except Exception as exc:
            logger.warning("Failed to enqueue invite email, skipping", extra={"invite_id": invite.id, "error": str(exc)})

    return invite


@router.get("/invites", response_model=list[InviteResponse])
async def api_list_invites(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, require_owner=True)
    return await list_invites(db, workspace_id)


@router.delete("/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_cancel_invite(
    workspace_id: str,
    invite_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, require_owner=True)
    invite = await cancel_invite(db, invite_id)
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")


@router.get("/members", response_model=list[MemberResponse])
async def api_list_members(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    return await list_members(db, workspace_id)


@router.delete("/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_remove_member(
    workspace_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await verify_workspace_access(db, workspace_id, current_user, require_owner=True)
    if user_id == ws.owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove workspace owner")
    removed = await remove_member(db, workspace_id, user_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")


@router.post("/invites/accept")
async def api_accept_invite(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    member = await accept_invite(db, token)
    if not member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired invite")
    return {"status": "accepted", "workspace_id": member.workspace_id}


@router.post("/invites/decline")
async def api_decline_invite(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    ok = await decline_invite(db, token)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invite")
    return {"status": "declined"}
