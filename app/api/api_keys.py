from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse, ApiKeyWithRaw
from app.services.api_key_service import (
    authenticate_api_key,
    create_api_key,
    list_api_keys,
    revoke_api_key,
)
from app.services.workspace_service import get_workspace

router = APIRouter(prefix="/workspaces/{workspace_id}/api-keys", tags=["api-keys"])


async def _verify_workspace_access(
    workspace_id: str, db: AsyncSession, user: User
) -> None:
    ws = await get_workspace(db, workspace_id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if ws.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not workspace owner")


@router.post("", response_model=ApiKeyWithRaw, status_code=status.HTTP_201_CREATED)
async def api_create_api_key(
    workspace_id: str,
    data: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_workspace_access(workspace_id, db, current_user)
    key_obj, raw_key = await create_api_key(db, data, current_user.id, workspace_id)
    return ApiKeyWithRaw(
        id=key_obj.id,
        prefix=key_obj.prefix,
        name=key_obj.name,
        workspace_id=key_obj.workspace_id,
        is_active=key_obj.is_active,
        created_at=key_obj.created_at,
        raw_key=raw_key,
    )


@router.get("", response_model=list[ApiKeyResponse])
async def api_list_api_keys(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_workspace_access(workspace_id, db, current_user)
    return await list_api_keys(db, workspace_id)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_revoke_api_key(
    workspace_id: str,
    key_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_workspace_access(workspace_id, db, current_user)
    key = await revoke_api_key(db, key_id)
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
