from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_db
from app.core.security import get_current_user, verify_password
from app.models.click import Click
from app.models.user import User
from app.schemas.click import ClickResponse
from app.schemas.link import LinkCreate, LinkResponse, LinkUpdate, PasswordVerifyRequest, PasswordVerifyResponse
from app.schemas.common import PaginatedResponse
from app.services.audit_service import log_audit_event
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
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, data.workspace_id, current_user, required_permission="links:create")
    link = await create_link(db, data, user_id=current_user.id)
    await log_audit_event(
        db,
        action="create",
        resource_type="link",
        resource_id=link.id,
        workspace_id=data.workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return link


@router.get("", response_model=PaginatedResponse)
async def api_list_links(
    workspace_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    folder_id: str | None = Query(None),
    is_archived: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="analytics:view")
    links, total, has_next = await get_links(db, workspace_id, page=page, page_size=page_size, search=search, folder_id=folder_id, is_archived=is_archived)
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        items=[LinkResponse.model_validate(l) for l in links],
    )


class BulkArchiveRequest(BaseModel):
    link_ids: list[str]
    is_archived: bool = True

class BulkFolderRequest(BaseModel):
    link_ids: list[str]
    folder_id: str | None = None

@router.post("/bulk-archive", status_code=status.HTTP_200_OK)
async def api_bulk_archive(
    data: BulkArchiveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from pydantic import BaseModel as _BM
    updated = 0
    for lid in data.link_ids:
        link = await get_link_by_id(db, lid)
        if not link:
            continue
        await verify_workspace_access(db, link.workspace_id, current_user, required_permission="links:update")
        link.is_archived = data.is_archived
        updated += 1
    await db.flush()
    return {"updated": updated}


@router.post("/bulk-move", status_code=status.HTTP_200_OK)
async def api_bulk_move(
    data: BulkFolderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = 0
    for lid in data.link_ids:
        link = await get_link_by_id(db, lid)
        if not link:
            continue
        await verify_workspace_access(db, link.workspace_id, current_user, required_permission="links:update")
        link.folder_id = data.folder_id
        updated += 1
    await db.flush()
    return {"updated": updated}


@router.post("/{link_id}/duplicate", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def api_duplicate_link(
    link_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, current_user, required_permission="links:create")
    from app.services.link_service import create_link as _create
    from app.schemas.link import LinkCreate
    dup = LinkCreate(destination_url=link.destination_url, title=(link.title + " (copy)" if link.title else None), workspace_id=link.workspace_id)
    new_link = await _create(db, dup, user_id=current_user.id)
    await log_audit_event(db, action="create", resource_type="link", resource_id=new_link.id, workspace_id=link.workspace_id, user_id=current_user.id, ip_address=request.client.host if request.client else None)
    return new_link


@router.get("/{link_id}", response_model=LinkResponse)
async def api_get_link(
    link_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, current_user, required_permission="analytics:view")
    return link


@router.patch("/{link_id}", response_model=LinkResponse)
async def api_update_link(
    link_id: str,
    data: LinkUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, current_user, required_permission="links:update")
    updated = await update_link(db, link, data)
    await log_audit_event(
        db,
        action="update",
        resource_type="link",
        resource_id=link.id,
        workspace_id=link.workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return updated


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_link(
    link_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, current_user, required_permission="links:delete")
    await delete_link(db, link)
    await log_audit_event(
        db,
        action="delete",
        resource_type="link",
        resource_id=link_id,
        workspace_id=link.workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )


@router.get("/{link_id}/qrcode")
async def api_link_qrcode(
    link_id: str,
    request: Request,
    format: str = Query("png", pattern="^(png|svg)$"),
    box_size: int = Query(10, ge=4, le=40),
    fill_color: str = Query("black", max_length=50),
    back_color: str = Query("white", max_length=50),
    error_correction: str = Query("M", pattern="^[LMQH]$"),
    style: str = Query("square", pattern="^(square|rounded)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, current_user, required_permission="analytics:view")

    short_url = f"{request.base_url.scheme}://{request.url.hostname}/{link.short_code}"

    if format == "svg":
        svg = generate_qr_svg(short_url, fill_color=fill_color, back_color=back_color, error_correction=error_correction)
        return Response(content=svg, media_type="image/svg+xml")
    png = generate_qr_png(short_url, box_size=box_size, fill_color=fill_color, back_color=back_color, error_correction=error_correction, style=style)
    return Response(content=png, media_type="image/png")


@router.get("/{link_id}/clicks", response_model=PaginatedResponse)
async def api_link_clicks(
    link_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, current_user, required_permission="analytics:view")

    count_result = await db.execute(
        select(func.count()).select_from(Click).where(Click.link_id == link_id)
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        select(Click)
        .where(Click.link_id == link_id)
        .order_by(Click.timestamp.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = [ClickResponse.model_validate(c) for c in result.scalars().all()]
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
        items=items,
    )


@router.get("/{link_id}/health")
async def api_link_health(
    link_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, current_user, required_permission="analytics:view")
    import httpx
    from app.core.security import validate_private_url
    try:
        validate_private_url(link.destination_url)
    except Exception as e:
        return {"link_id": link_id, "status": "blocked", "reason": str(e), "checked_at": link.updated_at}
    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            resp = await client.head(link.destination_url)
            code = resp.status_code
            healthy = 200 <= code < 400
            return {"link_id": link_id, "status": "healthy" if healthy else "unhealthy", "http_code": code, "checked_at": link.updated_at}
    except Exception as e:
        return {"link_id": link_id, "status": "error", "reason": str(e)[:200], "checked_at": link.updated_at}


@router.post("/{link_id}/verify-password", response_model=PasswordVerifyResponse)
async def api_verify_link_password(
    link_id: str,
    data: PasswordVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    from app.core.rate_limiter import _check_rate_limit, ZONES
    zone = "_pw_verify"
    if zone not in ZONES:
        ZONES[zone] = {"max": 5, "window": 60}
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (request.client.host if request.client else "unknown")
    allowed, _, _ = await _check_rate_limit(f"rl:pw:{client_ip}:{link_id}", zone)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many password attempts")
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    if not link.password_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Link is not password protected")
    if not verify_password(data.password, link.password_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid password")
    return PasswordVerifyResponse(destination_url=link.destination_url)
