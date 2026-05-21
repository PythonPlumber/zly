from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_db
from app.core.security import get_current_user, verify_password
from app.models.user import User
from app.schemas.link import LinkCreate, LinkResponse, LinkUpdate, PasswordVerifyRequest, PasswordVerifyResponse
from app.services.link_service import (
    create_link,
    delete_link,
    get_link_by_id,
    get_links,
    update_link,
)
from app.services.qr_service import generate_qr_png, generate_qr_svg
from app.services.workspace_service import verify_workspace_access

router = APIRouter()


@router.post("", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def api_create_link(
    data: LinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, data.workspace_id, current_user)
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
    await verify_workspace_access(db, workspace_id, current_user)
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
    await verify_workspace_access(db, link.workspace_id, current_user)
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
    await verify_workspace_access(db, link.workspace_id, current_user)
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
    await verify_workspace_access(db, link.workspace_id, current_user)
    await delete_link(db, link)


@router.get("/{link_id}/qrcode")
async def api_link_qrcode(
    link_id: str,
    format: str = Query("png", pattern="^(png|svg)$"),
    box_size: int = Query(10, ge=4, le=40),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, current_user)

    short_url = f"http://{settings.default_domain}/{link.short_code}"

    if format == "svg":
        svg = generate_qr_svg(short_url)
        return Response(content=svg, media_type="image/svg+xml")
    png = generate_qr_png(short_url, box_size=box_size)
    return Response(content=png, media_type="image/png")


@router.post("/{link_id}/verify-password", response_model=PasswordVerifyResponse)
async def api_verify_link_password(
    link_id: str,
    data: PasswordVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    if not link.password_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Link is not password protected")
    if not verify_password(data.password, link.password_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid password")
    return PasswordVerifyResponse(destination_url=link.destination_url)
