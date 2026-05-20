from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_workspace(db, data, current_user.id)


@router.get("", response_model=list[WorkspaceResponse])
async def api_list_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_workspaces_for_user(db, current_user.id)


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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await verify_workspace_access(db, workspace_id, current_user, require_owner=True)
    return await update_workspace(db, ws, data)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await verify_workspace_access(db, workspace_id, current_user, require_owner=True)
    await delete_workspace(db, ws)
