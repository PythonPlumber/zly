import hashlib
import hmac
import json
from collections.abc import Sequence

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import Webhook
from app.schemas.webhook import WebhookCreate, WebhookUpdate


async def create_webhook(db: AsyncSession, workspace_id: str, data: WebhookCreate) -> Webhook:
    wh = Webhook(
        workspace_id=workspace_id,
        name=data.name,
        url=data.url,
        secret=data.secret,
        events=data.events,
        is_active=data.is_active,
    )
    db.add(wh)
    await db.flush()
    await db.refresh(wh)
    return wh


async def get_webhooks(db: AsyncSession, workspace_id: str, page: int = 1, page_size: int = 50) -> tuple[Sequence[Webhook], int, bool]:
    base = select(Webhook).where(Webhook.workspace_id == workspace_id).order_by(Webhook.created_at.desc())
    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    webhooks = result.scalars().all()
    has_next = (offset + page_size) < total
    return webhooks, total, has_next


async def get_webhook(db: AsyncSession, webhook_id: str) -> Webhook | None:
    result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
    return result.scalar_one_or_none()


async def update_webhook(db: AsyncSession, wh: Webhook, data: WebhookUpdate) -> Webhook:
    for field in ("name", "url", "secret", "events", "is_active"):
        value = getattr(data, field, None)
        if value is not None:
            setattr(wh, field, value)
    await db.flush()
    await db.refresh(wh)
    return wh


async def delete_webhook(db: AsyncSession, wh: Webhook) -> None:
    await db.delete(wh)


def _sign_payload(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


async def trigger_webhooks(
    db: AsyncSession,
    workspace_id: str,
    event: str,
    payload: dict,
) -> list[dict]:
    result = await db.execute(
        select(Webhook).where(
            Webhook.workspace_id == workspace_id,
            Webhook.is_active == True,
        )
    )
    webhooks = result.scalars().all()

    results = []

    for wh in webhooks:
        if not wh.has_event(event):
            continue

        from app.services.webhook_delivery_service import create_webhook_delivery

        delivery = await create_webhook_delivery(db, wh.id, event, payload)

        try:
            from app.core.arq_pool import get_arq_pool
            pool = await get_arq_pool()
            await pool.enqueue_job("deliver_webhook", delivery_id=delivery.id)
            results.append({"webhook_id": wh.id, "status": "enqueued", "delivery_id": delivery.id})
        except Exception as exc:
            from app.services.webhook_delivery_service import deliver_webhook as sync_deliver
            await sync_deliver(db, delivery.id)
            results.append({"webhook_id": wh.id, "status": "delivered_sync", "delivery_id": delivery.id})

    return results
