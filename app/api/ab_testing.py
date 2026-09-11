from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.ab import ABVariantCreate, ABVariantResponse, ABVariantUpdate
from app.schemas.common import PaginatedResponse
from app.services.ab_service import create_variant, delete_variant, get_variant, list_variants, update_variant
from app.services.audit_service import log_audit_event
from app.services.link_service import get_link_by_id
from app.services.workspace_service import verify_workspace_access

router = APIRouter()


@router.post("/links/{link_id}/variants", response_model=ABVariantResponse, status_code=201)
async def add_variant(
    link_id: str,
    data: ABVariantCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, user, require_owner=True, required_permission="links:update")
    variant = await create_variant(db, link_id, data)
    await log_audit_event(
        db,
        action="create",
        resource_type="ab_variant",
        resource_id=variant.id,
        workspace_id=link.workspace_id,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return variant


@router.get("/links/{link_id}/variants", response_model=PaginatedResponse)
async def get_variants(
    link_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, user, required_permission="links:update")
    variants, total, has_next = await list_variants(db, link_id, page=page, page_size=page_size)
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        items=[ABVariantResponse.model_validate(v) for v in variants],
    )


@router.put("/links/{link_id}/variants/{variant_id}", response_model=ABVariantResponse)
async def edit_variant(
    link_id: str,
    variant_id: str,
    data: ABVariantUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, user, require_owner=True, required_permission="links:update")
    variant = await update_variant(db, variant_id, data)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    await log_audit_event(
        db,
        action="update",
        resource_type="ab_variant",
        resource_id=variant_id,
        workspace_id=link.workspace_id,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return variant


@router.delete("/links/{link_id}/variants/{variant_id}", status_code=204)
async def remove_variant(
    link_id: str,
    variant_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, user, require_owner=True, required_permission="links:update")
    deleted = await delete_variant(db, variant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Variant not found")
    await log_audit_event(
        db,
        action="delete",
        resource_type="ab_variant",
        resource_id=variant_id,
        workspace_id=link.workspace_id,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
