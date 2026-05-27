from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
from app.services.audit_service import log_audit_event
from app.services.workspace_service import (
    create_workspace,
    delete_workspace,
    get_workspace,
    get_workspaces_for_user,
    update_workspace,
    verify_workspace_access,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def api_create_workspace(
    data: WorkspaceCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await create_workspace(db, data, current_user.id)
    await log_audit_event(
        db,
        action="create",
        resource_type="workspace",
        resource_id=ws.id,
        workspace_id=ws.id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return ws


@router.get("", response_model=PaginatedResponse)
async def api_list_workspaces(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspaces, total, has_next = await get_workspaces_for_user(db, current_user.id, page=page, page_size=page_size)
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        items=[WorkspaceResponse.model_validate(w) for w in workspaces],
    )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def api_get_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await verify_workspace_access(db, workspace_id, current_user)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def api_update_workspace(
    workspace_id: str,
    data: WorkspaceUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await verify_workspace_access(db, workspace_id, current_user, require_owner=True, required_permission="workspace:update")
    updated = await update_workspace(db, ws, data)
    await log_audit_event(
        db,
        action="update",
        resource_type="workspace",
        resource_id=workspace_id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return updated


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_workspace(
    workspace_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await verify_workspace_access(db, workspace_id, current_user, require_owner=True, required_permission="workspace:delete")
    await delete_workspace(db, ws)
    await log_audit_event(
        db,
        action="delete",
        resource_type="workspace",
        resource_id=workspace_id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
