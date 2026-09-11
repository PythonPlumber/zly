from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.audit import AuditLogResponse, PaginatedAuditLogs
from app.services.audit_service import get_audit_logs
from app.services.workspace_service import verify_workspace_access

router = APIRouter(tags=["audit"])


@router.get("/workspaces/{workspace_id}/audit-logs", response_model=PaginatedAuditLogs)
async def api_list_audit_logs(
    workspace_id: str,
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, require_owner=True, required_permission="audit:view")
    items, total = await get_audit_logs(
        db,
        workspace_id=workspace_id,
        action=action,
        resource_type=resource_type,
        page=page,
        page_size=page_size,
    )
    offset = (page - 1) * page_size
    return PaginatedAuditLogs(
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
        items=[AuditLogResponse.model_validate(i) for i in items],
    )
