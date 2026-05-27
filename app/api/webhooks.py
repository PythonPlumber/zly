from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.webhook import WebhookCreate, WebhookResponse, WebhookUpdate
from app.schemas.webhook_delivery import WebhookDeliveryListResponse, WebhookDeliveryResponse
from app.services.audit_service import log_audit_event
from app.services.webhook_service import (
    create_webhook,
    delete_webhook,
    get_webhook,
    get_webhooks,
    update_webhook,
)
from app.services.webhook_delivery_service import get_deliveries
from app.services.workspace_service import verify_workspace_access

router = APIRouter(prefix="/workspaces/{workspace_id}/webhooks", tags=["webhooks"])


@router.post("", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def api_create_webhook(
    workspace_id: str,
    data: WebhookCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, require_owner=True, required_permission="webhooks:manage")
    wh = await create_webhook(db, workspace_id, data)
    await log_audit_event(
        db,
        action="create",
        resource_type="webhook",
        resource_id=wh.id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return wh


@router.get("", response_model=PaginatedResponse)
async def api_list_webhooks(
    workspace_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="webhooks:manage")
    webhooks, total, has_next = await get_webhooks(db, workspace_id, page=page, page_size=page_size)
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        items=[WebhookResponse.model_validate(w) for w in webhooks],
    )


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def api_get_webhook(
    workspace_id: str,
    webhook_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="webhooks:manage")
    wh = await get_webhook(db, webhook_id)
    if not wh or wh.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
    return wh


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def api_update_webhook(
    workspace_id: str,
    webhook_id: str,
    data: WebhookUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, require_owner=True, required_permission="webhooks:manage")
    wh = await get_webhook(db, webhook_id)
    if not wh or wh.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
    updated = await update_webhook(db, wh, data)
    await log_audit_event(
        db,
        action="update",
        resource_type="webhook",
        resource_id=webhook_id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return updated


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_webhook(
    workspace_id: str,
    webhook_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, require_owner=True, required_permission="webhooks:manage")
    wh = await get_webhook(db, webhook_id)
    if not wh or wh.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
    await delete_webhook(db, wh)
    await log_audit_event(
        db,
        action="delete",
        resource_type="webhook",
        resource_id=webhook_id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )


@router.get("/{webhook_id}/deliveries", response_model=WebhookDeliveryListResponse)
async def api_list_webhook_deliveries(
    workspace_id: str,
    webhook_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="webhooks:manage")
    wh = await get_webhook(db, webhook_id)
    if not wh or wh.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    deliveries, total = await get_deliveries(db, webhook_id, page=page, page_size=page_size)
    has_next = (page * page_size) < total

    return WebhookDeliveryListResponse(
        deliveries=[WebhookDeliveryResponse.model_validate(d) for d in deliveries],
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
    )
