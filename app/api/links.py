from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.link import LinkCreate, LinkResponse, LinkUpdate
from app.services.link_service import (
    create_link,
    delete_link,
    get_link_by_id,
    get_links,
    update_link,
)

router = APIRouter()


@router.post("", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def api_create_link(data: LinkCreate, db: AsyncSession = Depends(get_db)):
    link = await create_link(db, data)
    return link


@router.get("", response_model=list[LinkResponse])
async def api_list_links(
    skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)
):
    links = await get_links(db, skip=skip, limit=limit)
    return links


@router.get("/{link_id}", response_model=LinkResponse)
async def api_get_link(link_id: str, db: AsyncSession = Depends(get_db)):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return link


@router.patch("/{link_id}", response_model=LinkResponse)
async def api_update_link(
    link_id: str, data: LinkUpdate, db: AsyncSession = Depends(get_db)
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return await update_link(db, link, data)


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_link(link_id: str, db: AsyncSession = Depends(get_db)):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await delete_link(db, link)
