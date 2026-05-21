from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.ab import ABVariantCreate, ABVariantResponse, ABVariantUpdate
from app.services.ab_service import create_variant, delete_variant, get_variant, list_variants, update_variant
from app.services.link_service import get_link_by_id
from app.services.workspace_service import verify_workspace_access

router = APIRouter()


@router.post("/links/{link_id}/variants", response_model=ABVariantResponse, status_code=201)
async def add_variant(
    link_id: str,
    data: ABVariantCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, user, require_owner=True)
    return await create_variant(db, link_id, data)


@router.get("/links/{link_id}/variants", response_model=list[ABVariantResponse])
async def get_variants(
    link_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, user)
    return await list_variants(db, link_id)


@router.put("/links/{link_id}/variants/{variant_id}", response_model=ABVariantResponse)
async def edit_variant(
    link_id: str,
    variant_id: str,
    data: ABVariantUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, user, require_owner=True)
    variant = await update_variant(db, variant_id, data)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    return variant


@router.delete("/links/{link_id}/variants/{variant_id}", status_code=204)
async def remove_variant(
    link_id: str,
    variant_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, user, require_owner=True)
    deleted = await delete_variant(db, variant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Variant not found")
