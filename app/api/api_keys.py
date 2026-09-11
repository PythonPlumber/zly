from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse, ApiKeyUpdate, ApiKeyWithRaw
from app.schemas.common import PaginatedResponse
from app.services.audit_service import log_audit_event
from app.services.api_key_service import (
    create_api_key,
    list_api_keys,
    revoke_api_key,
)
from app.services.workspace_service import verify_workspace_access

router = APIRouter(prefix="/workspaces/{workspace_id}/api-keys", tags=["api-keys"])


@router.post("", response_model=ApiKeyWithRaw, status_code=status.HTTP_201_CREATED)
async def api_create_api_key(
    workspace_id: str,
    data: ApiKeyCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, require_owner=True, required_permission="api_keys:manage")
    key_obj, raw_key = await create_api_key(db, data, current_user.id, workspace_id)
    await log_audit_event(
        db,
        action="create",
        resource_type="api_key",
        resource_id=key_obj.id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return ApiKeyWithRaw(
        id=key_obj.id,
        prefix=key_obj.prefix,
        name=key_obj.name,
        workspace_id=key_obj.workspace_id,
        is_active=key_obj.is_active,
        created_at=key_obj.created_at,
        raw_key=raw_key,
    )


@router.get("", response_model=PaginatedResponse)
async def api_list_api_keys(
    workspace_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, require_owner=True, required_permission="api_keys:manage")
    keys, total, has_next = await list_api_keys(db, workspace_id, page=page, page_size=page_size)
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        items=[ApiKeyResponse.model_validate(k) for k in keys],
    )


@router.patch("/{key_id}")
async def api_update_api_key(
    workspace_id: str,
    key_id: str,
    data: ApiKeyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.api_key_service import get_api_key
    await verify_workspace_access(db, workspace_id, current_user, require_owner=True, required_permission="api_keys:manage")
    key = await get_api_key(db, key_id)
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(key, field, value)
    await db.flush()
    return {"status": "updated"}


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_revoke_api_key(
    workspace_id: str,
    key_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, require_owner=True, required_permission="api_keys:manage")
    key = await revoke_api_key(db, key_id)
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    await log_audit_event(
        db,
        action="delete",
        resource_type="api_key",
        resource_id=key_id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
