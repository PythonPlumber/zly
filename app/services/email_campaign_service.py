import uuid
import re
from datetime import datetime, timezone

from sqlalchemy import distinct, select, func, update
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger

logger = get_logger(__name__)

from app.models.email_campaign import (
    EmailContact,
    EmailTemplate,
    EmailCampaign,
    EmailCampaignContact,
    EmailCampaignOpen,
    EmailCampaignClick,
)
from app.schemas.email_campaign import (
    EmailContactCreate,
    EmailTemplateCreate,
    EmailTemplateUpdate,
    EmailCampaignCreate,
    EmailCampaignUpdate,
)


async def create_contact(db: AsyncSession, workspace_id: str, data: EmailContactCreate) -> EmailContact:
    existing = await db.execute(
        select(EmailContact).where(
            EmailContact.workspace_id == workspace_id,
            EmailContact.email == data.email,
        )
    )
    contact = existing.scalar_one_or_none()
    if contact:
        return contact
    contact = EmailContact(
        workspace_id=workspace_id,
        email=data.email,
        status="active",
    )
    db.add(contact)
    await db.flush()
    await db.refresh(contact)
    return contact


async def list_contacts(db: AsyncSession, workspace_id: str, page: int = 1, page_size: int = 50) -> tuple[Sequence[EmailContact], int, bool]:
    base = select(EmailContact).where(EmailContact.workspace_id == workspace_id).order_by(EmailContact.created_at.desc())
    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    contacts = result.scalars().all()
    has_next = (offset + page_size) < total
    return contacts, total, has_next


async def delete_contact(db: AsyncSession, workspace_id: str, contact_id: str) -> bool:
    result = await db.execute(
        select(EmailContact).where(
            EmailContact.id == contact_id,
            EmailContact.workspace_id == workspace_id,
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        return False
    await db.delete(contact)
    await db.flush()
    return True


async def unsubscribe_contact(db: AsyncSession, contact_id: str) -> bool:
    result = await db.execute(select(EmailContact).where(EmailContact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        return False
    contact.status = "unsubscribed"
    contact.unsubscribed_at = datetime.now(timezone.utc)
    await db.flush()
    return True


async def create_template(
    db: AsyncSession, workspace_id: str, data: EmailTemplateCreate
) -> EmailTemplate:
    if data.is_default:
        await db.execute(
            update(EmailTemplate)
            .where(
                EmailTemplate.workspace_id == workspace_id,
                EmailTemplate.is_default == True,
            )
            .values(is_default=False)
        )
    template = EmailTemplate(
        workspace_id=workspace_id,
        name=data.name,
        subject=data.subject,
        html_body=data.html_body,
        is_default=data.is_default,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return template


async def list_templates(db: AsyncSession, workspace_id: str, page: int = 1, page_size: int = 50) -> tuple[Sequence[EmailTemplate], int, bool]:
    base = select(EmailTemplate).where(EmailTemplate.workspace_id == workspace_id).order_by(EmailTemplate.created_at.desc())
    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    templates = result.scalars().all()
    has_next = (offset + page_size) < total
    return templates, total, has_next


async def get_template(db: AsyncSession, template_id: str) -> EmailTemplate | None:
    result = await db.execute(select(EmailTemplate).where(EmailTemplate.id == template_id))
    return result.scalar_one_or_none()


async def update_template(
    db: AsyncSession, template: EmailTemplate, data: EmailTemplateUpdate
) -> EmailTemplate:
    if data.is_default and not template.is_default:
        await db.execute(
            update(EmailTemplate)
            .where(
                EmailTemplate.workspace_id == template.workspace_id,
                EmailTemplate.is_default == True,
            )
            .values(is_default=False)
        )
    for field in ("name", "subject", "html_body", "is_default"):
        value = getattr(data, field, None)
        if value is not None:
            setattr(template, field, value)
    await db.flush()
    await db.refresh(template)
    return template


async def delete_template(db: AsyncSession, template_id: str) -> bool:
    result = await db.execute(select(EmailTemplate).where(EmailTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        return False
    await db.delete(template)
    await db.flush()
    return True


async def create_campaign(
    db: AsyncSession, workspace_id: str, data: EmailCampaignCreate
) -> EmailCampaign:
    campaign = EmailCampaign(
        workspace_id=workspace_id,
        name=data.name,
        subject=data.subject,
        html_body=data.html_body,
        from_email=data.from_email,
        from_name=data.from_name,
        scheduled_at=data.scheduled_at,
        status="draft",
        stats={"sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "bounced": 0, "unsubscribed": 0},
    )
    db.add(campaign)
    await db.flush()
    await db.refresh(campaign)
    return campaign


async def list_campaigns(db: AsyncSession, workspace_id: str, page: int = 1, page_size: int = 50) -> tuple[Sequence[EmailCampaign], int, bool]:
    base = select(EmailCampaign).where(EmailCampaign.workspace_id == workspace_id).order_by(EmailCampaign.created_at.desc())
    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    campaigns = result.scalars().all()
    has_next = (offset + page_size) < total
    return campaigns, total, has_next


async def get_campaign(db: AsyncSession, campaign_id: str) -> EmailCampaign | None:
    result = await db.execute(select(EmailCampaign).where(EmailCampaign.id == campaign_id))
    return result.scalar_one_or_none()


async def update_campaign(
    db: AsyncSession, campaign: EmailCampaign, data: EmailCampaignUpdate
) -> EmailCampaign:
    for field in ("name", "subject", "html_body", "from_email", "from_name", "status"):
        value = getattr(data, field, None)
        if value is not None:
            setattr(campaign, field, value)
    await db.flush()
    await db.refresh(campaign)
    return campaign


async def delete_campaign(db: AsyncSession, campaign_id: str) -> bool:
    result = await db.execute(select(EmailCampaign).where(EmailCampaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        return False
    await db.delete(campaign)
    await db.flush()
    return True


async def record_open(
    db: AsyncSession, campaign_id: str, contact_id: str, ip_hash: str | None = None, user_agent: str | None = None
) -> EmailCampaignOpen:
    open_record = EmailCampaignOpen(
        campaign_id=campaign_id,
        contact_id=contact_id,
        ip_hash=ip_hash,
        user_agent=user_agent,
    )
    db.add(open_record)
    await db.flush()
    return open_record


async def record_click(
    db: AsyncSession, campaign_id: str, contact_id: str, link_id: str | None = None, ip_hash: str | None = None, user_agent: str | None = None
) -> EmailCampaignClick:
    click_record = EmailCampaignClick(
        campaign_id=campaign_id,
        contact_id=contact_id,
        link_id=link_id,
        ip_hash=ip_hash,
        user_agent=user_agent,
    )
    db.add(click_record)
    await db.flush()
    return click_record


def rewrite_links_with_tracking(html_body: str, base_url: str, campaign_id: str) -> str:
    url_pattern = re.compile(r'href=["\'](https?://[^"\']+)["\']')
    def replace_url(match):
        original_url = match.group(1)
        separator = "&" if "?" in original_url else "?"
        tracked_url = f"{base_url}/l/track/{campaign_id}?url={original_url}"
        return f'href="{tracked_url}"'
    return url_pattern.sub(replace_url, html_body)


def inject_open_tracking_pixel(html_body: str, base_url: str, campaign_id: str, contact_id: str) -> str:
    pixel_url = f"{base_url}/track/open/{campaign_id}/{contact_id}.gif"
    pixel_html = f'<img src="{pixel_url}" width="1" height="1" style="display:none" alt="" />'
    if "</body>" in html_body:
        return html_body.replace("</body>", f"{pixel_html}</body>")
    return html_body + pixel_html


async def update_campaign_stats(db: AsyncSession, campaign_id: str) -> None:
    sent_result = await db.execute(
        select(func.count()).select_from(EmailCampaignContact).where(EmailCampaignContact.campaign_id == campaign_id)
    )
    sent = sent_result.scalar() or 0

    opens_result = await db.execute(
        select(func.count(distinct(EmailCampaignOpen.contact_id)))
        .where(EmailCampaignOpen.campaign_id == campaign_id)
    )
    opened = opens_result.scalar() or 0

    clicks_result = await db.execute(
        select(func.count(distinct(EmailCampaignClick.contact_id)))
        .where(EmailCampaignClick.campaign_id == campaign_id)
    )
    clicked = clicks_result.scalar() or 0

    campaign = await get_campaign(db, campaign_id)
    if campaign:
        campaign.stats = {
            "sent": sent,
            "delivered": sent,
            "opened": opened,
            "clicked": clicked,
            "bounced": 0,
            "unsubscribed": 0,
        }
        await db.flush()


async def send_campaign_sync(
    db: AsyncSession,
    campaign_id: str,
    contact_ids: list[str],
    base_url: str,
) -> dict:
    from app.core.email import get_email_backend
    from app.models.email_campaign import EmailCampaignContact as ECC

    try:
        campaign_obj = await get_campaign(db, campaign_id)
        if campaign_obj:
            from app.services.webhook_service import trigger_webhooks
            await trigger_webhooks(db, campaign_obj.workspace_id, "campaign.sent", {
                "event": "campaign.sent",
                "campaign_id": campaign_id,
                "workspace_id": campaign_obj.workspace_id,
                "campaign_name": campaign_obj.name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    except Exception:
        pass

    campaign = await get_campaign(db, campaign_id)
    if not campaign:
        return {"status": "error", "message": "Campaign not found"}

    campaign.status = "sending"
    await db.flush()

    if not contact_ids:
        from app.models.email_campaign import EmailContact
        contacts_result = await db.execute(
            select(EmailContact).where(
                EmailContact.workspace_id == campaign.workspace_id,
                EmailContact.status == "active",
            )
        )
        contacts = contacts_result.scalars().all()
    else:
        from app.models.email_campaign import EmailContact
        contacts_result = await db.execute(
            select(EmailContact).where(
                EmailContact.id.in_(contact_ids),
                EmailContact.workspace_id == campaign.workspace_id,
            )
        )
        contacts = contacts_result.scalars().all()

    backend = get_email_backend()
    tracked_html = rewrite_links_with_tracking(campaign.html_body, base_url, campaign_id)

    from_email = campaign.from_email or backend.from_email
    from_name = campaign.from_name or backend.from_name

    sent_count = 0
    for contact in contacts:
        try:
            await backend.send_email(
                to=contact.email,
                subject=campaign.subject,
                html_body=inject_open_tracking_pixel(tracked_html, base_url, campaign_id, contact.id),
                from_email=from_email,
                from_name=from_name,
            )
            sent_count += 1
        except Exception as exc:
            logger.warning("Failed to send campaign email", extra={"contact_id": contact.id, "error": str(exc)})

        link_entry = EmailCampaignContact(campaign_id=campaign_id, contact_id=contact.id)
        db.add(link_entry)

    campaign.status = "sent" if sent_count > 0 else "failed"
    campaign.sent_at = datetime.now(timezone.utc) if sent_count > 0 else None
    await db.flush()

    await update_campaign_stats(db, campaign_id)
    await db.commit()

    return {"status": campaign.status, "contacts": sent_count}