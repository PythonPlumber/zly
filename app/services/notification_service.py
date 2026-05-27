from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.click import Click
from app.models.link import Link
from app.models.user import User
from app.models.workspace import Workspace


logger = get_logger(__name__)
from app.services.webhook_service import trigger_webhooks


async def check_expiring_links(
    db: AsyncSession, workspace_id: str, within_hours: int = 24
) -> list[dict]:
    cutoff = datetime.now(timezone.utc) + timedelta(hours=within_hours)
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Link).where(
            Link.workspace_id == workspace_id,
            Link.expires_at.isnot(None),
            Link.expires_at <= cutoff,
            Link.expires_at > now,
            Link.is_active == True,
        )
    )
    links = result.scalars().all()

    ws_result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    ws = ws_result.scalar_one_or_none()
    owner_email = None
    if ws:
        user_result = await db.execute(select(User).where(User.id == ws.owner_id))
        owner = user_result.scalar_one_or_none()
        if owner:
            owner_email = owner.email

    fired = []
    for link in links:
        if link.last_notified_at and link.last_notified_at >= now - timedelta(hours=within_hours):
            continue
        payload = {
            "event": "link.expiring_soon",
            "link_id": link.id,
            "short_code": link.short_code,
            "title": link.title,
            "destination_url": link.destination_url,
            "expires_at": str(link.expires_at),
        }
        await trigger_webhooks(db, workspace_id, "link.expiring_soon", payload)

        if owner_email:
            expires_at_naive = link.expires_at.replace(tzinfo=None) if link.expires_at.tzinfo else link.expires_at
            now_naive = now.replace(tzinfo=None)
            hours_remaining = int((expires_at_naive - now_naive).total_seconds() / 3600)
            click_count_result = await db.execute(
                select(func.count()).select_from(Click).where(Click.link_id == link.id)
            )
            total_clicks = click_count_result.scalar() or 0
            try:
                from app.core.arq_pool import get_arq_pool
                from app.config import settings
                pool = await get_arq_pool()
                await pool.enqueue_job(
                    "send_expiry_alert_email_job",
                    link_id=link.id,
                    to_email=owner_email,
                    link_title=link.title or link.short_code,
                    short_code=link.short_code,
                    short_url=f"{settings.default_domain}/{link.short_code}",
                    destination_url=link.destination_url,
                    expires_at=str(link.expires_at),
                    hours_remaining=hours_remaining,
                    total_clicks=total_clicks,
                )
            except Exception as exc:
                logger.warning("Failed to enqueue expiry alert email", extra={"link_id": link.id, "error": str(exc)})

        link.last_notified_at = now
        fired.append(payload)
    await db.flush()
    return fired
