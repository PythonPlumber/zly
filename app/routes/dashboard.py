from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user_from_cookie as get_current_user
from app.models.user import User
from app.services.bio_service import get_bio_page, get_bio_page_by_slug
from app.services.link_service import get_link_by_id
from app.services.workspace_service import get_workspace, get_workspaces_for_user

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "dashboard/index.html",
        {"user": current_user, "default_ws": default_ws},
    )


@router.get("/dashboard/links", response_class=HTMLResponse)
async def links_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        request, "dashboard/links.html",
        {"user": current_user},
    )


@router.get("/dashboard/links/{link_id}", response_class=HTMLResponse)
async def link_detail_page(
    request: Request,
    link_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=404)
    ws = await get_workspace(db, link.workspace_id)
    if not ws or ws.owner_id != current_user.id:
        raise HTTPException(status_code=403)
    return templates.TemplateResponse(
        request, "dashboard/link_detail.html",
        {"user": current_user, "link": link},
    )


@router.get("/dashboard/bio", response_class=HTMLResponse)
async def bio_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    bio = None
    if default_ws:
        bio = await get_bio_page(db, default_ws.id)
    return templates.TemplateResponse(
        request, "dashboard/bio.html",
        {"user": current_user, "bio": bio, "workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        request, "dashboard/settings.html",
        {"user": current_user},
    )


@router.get("/dashboard/domains", response_class=HTMLResponse)
async def domains_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "dashboard/domains.html",
        {"user": current_user, "workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/api-keys", response_class=HTMLResponse)
async def api_keys_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "dashboard/api_keys.html",
        {"user": current_user, "workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/webhooks", response_class=HTMLResponse)
async def webhooks_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "dashboard/webhooks.html",
        {"user": current_user, "workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/tags", response_class=HTMLResponse)
async def tags_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "dashboard/tags.html",
        {"user": current_user, "workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/bio/{slug}", response_class=HTMLResponse)
async def public_bio_page(
    request: Request,
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    bio = await get_bio_page_by_slug(db, slug)
    if not bio or not bio.is_published:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "bio/public.html",
        {"bio": bio},
    )
