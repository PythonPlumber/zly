from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.bio_service import get_bio_page
from app.services.link_service import get_link_by_id, get_links
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
        "dashboard/index.html",
        {"request": request, "user": current_user, "default_ws": default_ws},
    )


@router.get("/dashboard/links", response_class=HTMLResponse)
async def links_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return templates.TemplateResponse(
        "dashboard/links.html",
        {"request": request, "user": current_user},
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
        "dashboard/link_detail.html",
        {"request": request, "user": current_user, "link": link},
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
        "dashboard/bio.html",
        {"request": request, "user": current_user, "bio": bio, "workspace_id": default_ws.id if default_ws else ""},
    )
