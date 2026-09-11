from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.folder import FolderCreate, FolderResponse
from app.services.folder_service import create_folder, delete_folder, get_folder, get_folders
from app.services.workspace_service import verify_workspace_access

router = APIRouter(prefix="/workspaces/{workspace_id}/folders", tags=["folders"])


@router.post("", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def api_create_folder(
    workspace_id: str,
    data: FolderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="links:create")
    if not data.name or not data.name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Folder name required")
    folder = await create_folder(db, workspace_id, data.name)
    return folder


@router.get("", response_model=list[FolderResponse])
async def api_list_folders(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="analytics:view")
    folders = await get_folders(db, workspace_id)
    return folders


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_folder(
    workspace_id: str,
    folder_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="links:delete")
    folder = await get_folder(db, folder_id)
    if not folder or folder.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
    await delete_folder(db, folder)
