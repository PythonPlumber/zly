from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.models.user import User
from app.services.audit_service import log_audit_event
from app.schemas.common import PaginatedResponse
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
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await verify_workspace_access(db, workspace_id, current_user, require_owner=True, required_permission="members:manage")
    invite = await create_invite(db, workspace_id, current_user.id, data.email, data.role)

    email_data = await get_invite_email_data(db, invite, settings.default_domain)
    if email_data:
        try:
            from app.core.arq_pool import get_arq_pool
            pool = await get_arq_pool()
            await pool.enqueue_job("send_invite_email_job", **email_data)
        except Exception as exc:
            logger.warning("Failed to enqueue invite email, skipping", extra={"invite_id": invite.id, "error": str(exc)})

    await log_audit_event(
        db,
        action="create",
        resource_type="invite",
        resource_id=invite.id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return invite


@router.get("/invites", response_model=PaginatedResponse)
async def api_list_invites(
    workspace_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, require_owner=True, required_permission="members:manage")
    invites, total, has_next = await list_invites(db, workspace_id, page=page, page_size=page_size)
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        items=[InviteResponse.model_validate(i) for i in invites],
    )


@router.delete("/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_cancel_invite(
    workspace_id: str,
    invite_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, require_owner=True, required_permission="members:manage")
    invite = await cancel_invite(db, invite_id)
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    await log_audit_event(
        db,
        action="delete",
        resource_type="invite",
        resource_id=invite_id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )


@router.get("/members", response_model=PaginatedResponse)
async def api_list_members(
    workspace_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="members:manage")
    members, total, has_next = await list_members(db, workspace_id, page=page, page_size=page_size)
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        items=[MemberResponse.model_validate(m) for m in members],
    )


@router.delete("/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_remove_member(
    workspace_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await verify_workspace_access(db, workspace_id, current_user, require_owner=True, required_permission="members:manage")
    if user_id == ws.owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove workspace owner")
    removed = await remove_member(db, workspace_id, user_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")


@router.post("/invites/accept")
async def api_accept_invite(
    request: Request,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member = await accept_invite(db, token, current_user)
    if not member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired invite")
    await log_audit_event(
        db,
        action="create",
        resource_type="member",
        resource_id=member.user_id,
        workspace_id=member.workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return {"status": "accepted", "workspace_id": member.workspace_id}


@router.post("/invites/decline")
async def api_decline_invite(
    request: Request,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = await decline_invite(db, token, current_user)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invite")
    await log_audit_event(
        db,
        action="delete",
        resource_type="invite",
        resource_id=token,
        workspace_id=None,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return {"status": "declined"}
