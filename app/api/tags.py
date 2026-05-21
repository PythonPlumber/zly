from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.tag import LinkTagRequest, TagCreate, TagResponse, TagUpdate
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    return await create_tag(db, workspace_id, data)


@router.get("/workspaces/{workspace_id}/tags", response_model=list[TagResponse], tags=["tags"])
async def api_list_tags(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    return await get_tags(db, workspace_id)


@router.patch("/tags/{tag_id}", response_model=TagResponse, tags=["tags"])
async def api_update_tag(
    tag_id: str,
    data: TagUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag = await get_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    await verify_workspace_access(db, tag.workspace_id, current_user)
    return await update_tag(db, tag, data)


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tags"])
async def api_delete_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag = await get_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    await verify_workspace_access(db, tag.workspace_id, current_user)
    await delete_tag(db, tag)


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
    await verify_workspace_access(db, link.workspace_id, current_user)
    await set_link_tags(db, link_id, data.tag_ids)
