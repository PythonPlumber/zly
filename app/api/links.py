from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.link import LinkCreate, LinkResponse, LinkUpdate
from app.services.link_service import (
    create_link,
    delete_link,
    get_link_by_id,
    get_links,
    update_link,
)
from app.services.workspace_service import get_workspace

router = APIRouter()


async def _verify_workspace_access(
    workspace_id: str, db: AsyncSession, user: User
) -> None:
    ws = await get_workspace(db, workspace_id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if ws.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not workspace owner")


@router.post("", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def api_create_link(
    data: LinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_workspace_access(data.workspace_id, db, current_user)
    link = await create_link(db, data, user_id=current_user.id)
    return link


@router.get("", response_model=list[LinkResponse])
async def api_list_links(
    workspace_id: str,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_workspace_access(workspace_id, db, current_user)
    links = await get_links(db, workspace_id, skip=skip, limit=limit)
    return links


@router.get("/{link_id}", response_model=LinkResponse)
async def api_get_link(
    link_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    ws = await get_workspace(db, link.workspace_id)
    if not ws or ws.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not workspace owner")
    return link


@router.patch("/{link_id}", response_model=LinkResponse)
async def api_update_link(
    link_id: str,
    data: LinkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    ws = await get_workspace(db, link.workspace_id)
    if not ws or ws.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not workspace owner")
    return await update_link(db, link, data)


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_link(
    link_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    ws = await get_workspace(db, link.workspace_id)
    if not ws or ws.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not workspace owner")
    await delete_link(db, link)
