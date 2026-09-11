from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.tag import LinkTagRequest, TagCreate, TagResponse, TagUpdate
from app.services.audit_service import log_audit_event
from app.services.link_service import get_link_by_id
from app.services.tag_service import (
    create_tag,
    delete_tag,
    get_tag,
    get_tags,
    set_link_tags,
    update_tag,
)
from app.services.workspace_service import verify_workspace_access

router = APIRouter()


@router.post("/workspaces/{workspace_id}/tags", response_model=TagResponse, status_code=status.HTTP_201_CREATED, tags=["tags"])
async def api_create_tag(
    workspace_id: str,
    data: TagCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="tags:manage")
    tag = await create_tag(db, workspace_id, data)
    await log_audit_event(
        db,
        action="create",
        resource_type="tag",
        resource_id=tag.id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return tag


@router.get("/workspaces/{workspace_id}/tags", response_model=PaginatedResponse, tags=["tags"])
async def api_list_tags(
    workspace_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="tags:manage")
    tags, total, has_next = await get_tags(db, workspace_id, page=page, page_size=page_size)
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        items=[TagResponse.model_validate(t) for t in tags],
    )


@router.get("/tags/{tag_id}", response_model=TagResponse, tags=["tags"])
async def api_get_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag = await get_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    await verify_workspace_access(db, tag.workspace_id, current_user, required_permission="tags:manage")
    return tag


@router.patch("/tags/{tag_id}", response_model=TagResponse, tags=["tags"])
async def api_update_tag(
    tag_id: str,
    data: TagUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag = await get_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    await verify_workspace_access(db, tag.workspace_id, current_user, required_permission="tags:manage")
    updated = await update_tag(db, tag, data)
    await log_audit_event(
        db,
        action="update",
        resource_type="tag",
        resource_id=tag_id,
        workspace_id=tag.workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return updated


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tags"])
async def api_delete_tag(
    tag_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag = await get_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    await verify_workspace_access(db, tag.workspace_id, current_user, required_permission="tags:manage")
    await delete_tag(db, tag)
    await log_audit_event(
        db,
        action="delete",
        resource_type="tag",
        resource_id=tag_id,
        workspace_id=tag.workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )


@router.post("/links/{link_id}/tags", status_code=status.HTTP_204_NO_CONTENT, tags=["tags"])
async def api_set_link_tags(
    link_id: str,
    data: LinkTagRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, current_user, required_permission="tags:manage")
    await set_link_tags(db, link_id, data.tag_ids)
