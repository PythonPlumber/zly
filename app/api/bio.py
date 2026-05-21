from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.user import User
from app.schemas.bio import (
    BioLinkCreate,
    BioLinkResponse,
    BioLinkUpdate,
    BioPageCreate,
    BioPagePublicResponse,
    BioPageResponse,
    BioPageUpdate,
)
from app.services.bio_service import (
    add_bio_link,
    create_bio_page,
    delete_bio_page,
    get_bio_page,
    get_bio_page_by_slug,
    remove_bio_link,
    reorder_bio_links,
    update_bio_link,
    update_bio_page,
)
from app.services.workspace_service import verify_workspace_access
from app.core.security import get_current_user

router = APIRouter()


@router.get("/bio/{slug}", response_model=BioPagePublicResponse)
async def get_public_bio_page(slug: str, db: AsyncSession = Depends(get_db)):
    bio = await get_bio_page_by_slug(db, slug)
    if not bio:
        raise HTTPException(status_code=404, detail="Bio page not found")
    return bio


@router.post("/workspaces/{workspace_id}/bio", response_model=BioPageResponse)
async def create_workspace_bio(
    workspace_id: str,
    data: BioPageCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, user, require_owner=True)
    existing = await get_bio_page(db, workspace_id)
    if existing:
        raise HTTPException(status_code=409, detail="Bio page already exists for this workspace")
    bio = await create_bio_page(db, workspace_id, data)
    return bio


@router.get("/workspaces/{workspace_id}/bio", response_model=BioPageResponse)
async def get_workspace_bio(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, user)
    bio = await get_bio_page(db, workspace_id)
    if not bio:
        raise HTTPException(status_code=404, detail="Bio page not found")
    return bio


@router.put("/workspaces/{workspace_id}/bio", response_model=BioPageResponse)
async def update_workspace_bio(
    workspace_id: str,
    data: BioPageUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, user, require_owner=True)
    bio = await update_bio_page(db, workspace_id, data)
    if not bio:
        raise HTTPException(status_code=404, detail="Bio page not found")
    return bio


@router.delete("/workspaces/{workspace_id}/bio")
async def delete_workspace_bio(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, user, require_owner=True)
    deleted = await delete_bio_page(db, workspace_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Bio page not found")
    return {"detail": "Bio page deleted"}


@router.post("/workspaces/{workspace_id}/bio/links", response_model=BioLinkResponse)
async def add_link_to_bio(
    workspace_id: str,
    data: BioLinkCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, user, require_owner=True)
    bio = await get_bio_page(db, workspace_id)
    if not bio:
        raise HTTPException(status_code=404, detail="Bio page not found")
    bio_link = await add_bio_link(db, bio.id, data)
    return bio_link


@router.put("/workspaces/{workspace_id}/bio/links/{link_id}", response_model=BioLinkResponse)
async def update_bio_link_endpoint(
    workspace_id: str,
    link_id: str,
    data: BioLinkUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, user, require_owner=True)
    bio_link = await update_bio_link(db, link_id, data)
    if not bio_link:
        raise HTTPException(status_code=404, detail="Bio link not found")
    return bio_link


@router.delete("/workspaces/{workspace_id}/bio/links/{link_id}")
async def remove_bio_link_endpoint(
    workspace_id: str,
    link_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, user, require_owner=True)
    deleted = await remove_bio_link(db, link_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Bio link not found")
    return {"detail": "Bio link removed"}


@router.put("/workspaces/{workspace_id}/bio/links/reorder")
async def reorder_bio_links_endpoint(
    workspace_id: str,
    link_ids: list[str],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, user, require_owner=True)
    bio = await get_bio_page(db, workspace_id)
    if not bio:
        raise HTTPException(status_code=404, detail="Bio page not found")
    links = await reorder_bio_links(db, bio.id, link_ids)
    return [BioLinkResponse.model_validate(l) for l in links]
