from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.email_campaign import (
    EmailCampaignCreate,
    EmailCampaignResponse,
    EmailCampaignStatsResponse,
    EmailCampaignUpdate,
    EmailContactCreate,
    EmailContactResponse,
    EmailTemplateCreate,
    EmailTemplateResponse,
    EmailTemplateUpdate,
)
from app.services.audit_service import log_audit_event
from app.services.email_campaign_service import (
    create_contact,
    create_campaign,
    create_template,
    delete_campaign,
    delete_contact,
    delete_template,
    get_campaign,
    get_template,
    list_campaigns,
    list_contacts,
    list_templates,
    rewrite_links_with_tracking,
    inject_open_tracking_pixel,
    update_campaign,
    update_campaign_stats,
    update_template,
)
from app.services.workspace_service import verify_workspace_access

logger = get_logger(__name__)

router = APIRouter(prefix="/workspaces/{workspace_id}/email", tags=["email_campaigns"])


@router.get("/contacts", response_model=PaginatedResponse)
async def api_list_contacts(
    workspace_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="campaigns:manage")
    contacts, total, has_next = await list_contacts(db, workspace_id, page=page, page_size=page_size)
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        items=[EmailContactResponse.model_validate(c) for c in contacts],
    )


@router.post("/contacts", response_model=EmailContactResponse, status_code=status.HTTP_201_CREATED)
async def api_create_contact(
    workspace_id: str,
    data: EmailContactCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="campaigns:manage")
    contact = await create_contact(db, workspace_id, data)
    await log_audit_event(
        db,
        action="create",
        resource_type="contact",
        resource_id=contact.id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return contact


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_contact(
    workspace_id: str,
    contact_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="campaigns:manage")
    deleted = await delete_contact(db, workspace_id, contact_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    await log_audit_event(
        db,
        action="delete",
        resource_type="contact",
        resource_id=contact_id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )


@router.get("/templates", response_model=PaginatedResponse)
async def api_list_templates(
    workspace_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="campaigns:manage")
    templates, total, has_next = await list_templates(db, workspace_id, page=page, page_size=page_size)
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        items=[EmailTemplateResponse.model_validate(t) for t in templates],
    )


@router.post("/templates", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
async def api_create_template(
    workspace_id: str,
    data: EmailTemplateCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="campaigns:manage")
    template = await create_template(db, workspace_id, data)
    await log_audit_event(
        db,
        action="create",
        resource_type="template",
        resource_id=template.id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return template


@router.get("/templates/{template_id}", response_model=EmailTemplateResponse)
async def api_get_template(
    workspace_id: str,
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="campaigns:manage")
    template = await get_template(db, template_id)
    if not template or template.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return template


@router.put("/templates/{template_id}", response_model=EmailTemplateResponse)
async def api_update_template(
    workspace_id: str,
    template_id: str,
    data: EmailTemplateUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="campaigns:manage")
    template = await get_template(db, template_id)
    if not template or template.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    updated = await update_template(db, template, data)
    await log_audit_event(
        db,
        action="update",
        resource_type="template",
        resource_id=template_id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return updated


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_template(
    workspace_id: str,
    template_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="campaigns:manage")
    deleted = await delete_template(db, template_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    await log_audit_event(
        db,
        action="delete",
        resource_type="template",
        resource_id=template_id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )


@router.get("/campaigns", response_model=PaginatedResponse)
async def api_list_campaigns(
    workspace_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="campaigns:manage")
    campaigns, total, has_next = await list_campaigns(db, workspace_id, page=page, page_size=page_size)
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        items=[EmailCampaignResponse.model_validate(c) for c in campaigns],
    )


@router.post("/campaigns", response_model=EmailCampaignResponse, status_code=status.HTTP_201_CREATED)
async def api_create_campaign(
    workspace_id: str,
    data: EmailCampaignCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="campaigns:manage")
    campaign = await create_campaign(db, workspace_id, data)
    await log_audit_event(
        db,
        action="create",
        resource_type="campaign",
        resource_id=campaign.id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return campaign


@router.get("/campaigns/{campaign_id}", response_model=EmailCampaignResponse)
async def api_get_campaign(
    workspace_id: str,
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="campaigns:manage")
    campaign = await get_campaign(db, campaign_id)
    if not campaign or campaign.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


@router.put("/campaigns/{campaign_id}", response_model=EmailCampaignResponse)
async def api_update_campaign(
    workspace_id: str,
    campaign_id: str,
    data: EmailCampaignUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="campaigns:manage")
    campaign = await get_campaign(db, campaign_id)
    if not campaign or campaign.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    updated = await update_campaign(db, campaign, data)
    await log_audit_event(
        db,
        action="update",
        resource_type="campaign",
        resource_id=campaign_id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return updated


@router.delete("/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_campaign(
    workspace_id: str,
    campaign_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="campaigns:manage")
    deleted = await delete_campaign(db, campaign_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    await log_audit_event(
        db,
        action="delete",
        resource_type="campaign",
        resource_id=campaign_id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )


@router.post("/campaigns/{campaign_id}/send", status_code=status.HTTP_202_ACCEPTED)
async def api_send_campaign(
    workspace_id: str,
    campaign_id: str,
    contact_ids: list[str] | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, require_owner=True, required_permission="campaigns:manage")
    campaign = await get_campaign(db, campaign_id)
    if not campaign or campaign.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    from app.config import settings
    try:
        from app.core.arq_pool import get_arq_pool
        pool = await get_arq_pool()
        await pool.enqueue_job(
            "send_campaign_job",
            campaign_id=campaign_id,
            contact_ids=contact_ids or [],
            base_url=settings.default_domain,
        )
    except Exception as exc:
        logger.warning("Failed to enqueue campaign send, sending sync", extra={"campaign_id": campaign_id, "error": str(exc)})
        from app.services.email_campaign_service import send_campaign_sync
        await send_campaign_sync(db, campaign_id, contact_ids or [], settings.default_domain)

    return {"status": "enqueued", "campaign_id": campaign_id}


@router.get("/campaigns/{campaign_id}/stats", response_model=EmailCampaignStatsResponse)
async def api_campaign_stats(
    workspace_id: str,
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="campaigns:manage")
    campaign = await get_campaign(db, campaign_id)
    if not campaign or campaign.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    await update_campaign_stats(db, campaign_id)
    campaign = await get_campaign(db, campaign_id)
    return EmailCampaignStatsResponse(**campaign.stats)