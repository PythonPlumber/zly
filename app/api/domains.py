from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.domain import DomainCreate, DomainResponse, DomainVerifyRequest
from app.services.audit_service import log_audit_event
from app.services.domain_service import (
    create_domain,
    delete_domain,
    get_domain,
    list_workspace_domains,
    verify_domain,
)
from app.services.workspace_service import verify_workspace_access

router = APIRouter()


@router.post("/workspaces/{workspace_id}/domains", response_model=DomainResponse, status_code=201)
async def add_domain(
    workspace_id: str,
    data: DomainCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, user, require_owner=True, required_permission="domains:manage")
    domain = await create_domain(db, workspace_id, data)
    if not domain:
        raise HTTPException(status_code=409, detail="Domain already registered")
    await log_audit_event(
        db,
        action="create",
        resource_type="domain",
        resource_id=domain.id,
        workspace_id=workspace_id,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return domain


@router.get("/workspaces/{workspace_id}/domains", response_model=PaginatedResponse)
async def list_domains(
    workspace_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, user, required_permission="domains:manage")
    domains, total, has_next = await list_workspace_domains(db, workspace_id, page=page, page_size=page_size)
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        items=[DomainResponse.model_validate(d) for d in domains],
    )


@router.post("/workspaces/{workspace_id}/domains/{domain_id}/verify", response_model=DomainResponse)
async def verify_domain_endpoint(
    workspace_id: str,
    domain_id: str,
    data: DomainVerifyRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, user, require_owner=True, required_permission="domains:manage")
    domain = await verify_domain(db, domain_id, data.verification_code)
    if not domain:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    return domain


@router.delete("/workspaces/{workspace_id}/domains/{domain_id}", status_code=204)
async def remove_domain(
    workspace_id: str,
    domain_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, user, require_owner=True, required_permission="domains:manage")
    deleted = await delete_domain(db, domain_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Domain not found")
    await log_audit_event(
        db,
        action="delete",
        resource_type="domain",
        resource_id=domain_id,
        workspace_id=workspace_id,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
