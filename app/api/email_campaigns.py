from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.models.user import User
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
from app.services.email_campaign_service import (
    create_contact,
    create_campaign,
    create_template,
    delete_campaign,
    delete_contact,
    delete_template,
    get_campaign,
    list_campaigns,
    list_contacts,
    list_templates,
    rewrite_links_with_tracking,
    inject_open_tracking_pixel,
    update_campaign,
    update_campaign_stats,
)
from app.services.workspace_service import verify_workspace_access

logger = get_logger(__name__)

router = APIRouter(prefix="/workspaces/{workspace_id}/email", tags=["email_campaigns"])


@router.get("/contacts", response_model=list[EmailContactResponse])
async def api_list_contacts(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    return await list_contacts(db, workspace_id)


@router.post("/contacts", response_model=EmailContactResponse, status_code=status.HTTP_201_CREATED)
async def api_create_contact(
    workspace_id: str,
    data: EmailContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    return await create_contact(db, workspace_id, data)


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_contact(
    workspace_id: str,
    contact_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    deleted = await delete_contact(db, workspace_id, contact_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")


@router.get("/templates", response_model=list[EmailTemplateResponse])
async def api_list_templates(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    return await list_templates(db, workspace_id)


@router.post("/templates", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
async def api_create_template(
    workspace_id: str,
    data: EmailTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    return await create_template(db, workspace_id, data)


@router.get("/templates/{template_id}", response_model=EmailTemplateResponse)
async def api_get_template(
    workspace_id: str,
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    template = await list_templates(db, workspace_id)
    for t in template:
        if t.id == template_id:
            return t
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")


@router.put("/templates/{template_id}", response_model=EmailTemplateResponse)
async def api_update_template(
    workspace_id: str,
    template_id: str,
    data: EmailTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.email_campaign_service import get_template
    await verify_workspace_access(db, workspace_id, current_user)
    template = await get_template(db, template_id)
    if not template or template.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return await update_template(db, template, data)


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_template(
    workspace_id: str,
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    deleted = await delete_template(db, template_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")


@router.get("/campaigns", response_model=list[EmailCampaignResponse])
async def api_list_campaigns(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    return await list_campaigns(db, workspace_id)


@router.post("/campaigns", response_model=EmailCampaignResponse, status_code=status.HTTP_201_CREATED)
async def api_create_campaign(
    workspace_id: str,
    data: EmailCampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    return await create_campaign(db, workspace_id, data)


@router.get("/campaigns/{campaign_id}", response_model=EmailCampaignResponse)
async def api_get_campaign(
    workspace_id: str,
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    campaign = await get_campaign(db, campaign_id)
    if not campaign or campaign.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


@router.put("/campaigns/{campaign_id}", response_model=EmailCampaignResponse)
async def api_update_campaign(
    workspace_id: str,
    campaign_id: str,
    data: EmailCampaignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    campaign = await get_campaign(db, campaign_id)
    if not campaign or campaign.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return await update_campaign(db, campaign, data)


@router.delete("/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_campaign(
    workspace_id: str,
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    deleted = await delete_campaign(db, campaign_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")


@router.post("/campaigns/{campaign_id}/send", status_code=status.HTTP_202_ACCEPTED)
async def api_send_campaign(
    workspace_id: str,
    campaign_id: str,
    contact_ids: list[str] | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, require_owner=True)
    campaign = await get_campaign(db, campaign_id)
    if not campaign or campaign.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    try:
        from app.core.arq_pool import get_arq_pool
        from app.config import settings
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
    await verify_workspace_access(db, workspace_id, current_user)
    campaign = await get_campaign(db, campaign_id)
    if not campaign or campaign.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    await update_campaign_stats(db, campaign_id)
    campaign = await get_campaign(db, campaign_id)
    return EmailCampaignStatsResponse(**campaign.stats)