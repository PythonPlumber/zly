from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.audit import AuditLog
from app.models.click import Click
from app.models.email_campaign import EmailCampaign, EmailContact
from app.models.link import Link
from app.models.user import User
from app.models.webhook import Webhook
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.audit import AuditLogResponse

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_superuser(current_user: User) -> None:
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superuser access required")


@router.get("/users")
async def admin_list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_superuser(current_user)
    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = result.scalars().all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": (offset + page_size) < total,
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "display_name": u.display_name,
                "is_superuser": u.is_superuser,
                "is_active": u.is_active,
                "created_at": str(u.created_at),
            }
            for u in users
        ],
    }


@router.get("/users/{user_id}")
async def admin_get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_superuser(current_user)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "is_superuser": user.is_superuser,
        "is_active": user.is_active,
        "oauth_provider": user.oauth_provider,
        "created_at": str(user.created_at),
    }


class AdminUserUpdate(BaseModel):
    is_superuser: bool | None = None
    is_active: bool | None = None


@router.patch("/users/{user_id}")
async def admin_update_user(
    user_id: str,
    data: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_superuser(current_user)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if data.is_superuser is not None:
        user.is_superuser = data.is_superuser
    if data.is_active is not None:
        user.is_active = data.is_active
    await db.flush()
    return {"status": "updated"}


@router.get("/stats")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_superuser(current_user)
    users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    workspaces = (await db.execute(select(func.count()).select_from(Workspace))).scalar() or 0
    links = (await db.execute(select(func.count()).select_from(Link))).scalar() or 0
    clicks = (await db.execute(select(func.count()).select_from(Click))).scalar() or 0
    webhooks = (await db.execute(select(func.count()).select_from(Webhook))).scalar() or 0
    members = (await db.execute(select(func.count()).select_from(WorkspaceMember))).scalar() or 0
    campaigns = (await db.execute(select(func.count()).select_from(EmailCampaign))).scalar() or 0
    contacts = (await db.execute(select(func.count()).select_from(EmailContact))).scalar() or 0
    audit = (await db.execute(select(func.count()).select_from(AuditLog))).scalar() or 0
    return {
        "users": users,
        "workspaces": workspaces,
        "links": links,
        "clicks": clicks,
        "webhooks": webhooks,
        "workspace_members": members,
        "email_campaigns": campaigns,
        "email_contacts": contacts,
        "audit_logs": audit,
    }


@router.get("/audit-logs")
async def admin_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_superuser(current_user)
    query = select(AuditLog)
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
    )
    items = [AuditLogResponse.model_validate(i) for i in result.scalars().all()]
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": (offset + page_size) < total,
        "items": items,
    }
