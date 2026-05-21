from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
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
        link.last_notified_at = now
        fired.append(payload)
    await db.flush()
    return fired
