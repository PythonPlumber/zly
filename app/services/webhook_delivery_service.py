import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import Webhook
from app.models.webhook_delivery import WebhookDelivery


def _sign_payload(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


_RETRY_DELAYS = [
    timedelta(minutes=1),
    timedelta(minutes=5),
    timedelta(minutes=30),
    timedelta(hours=2),
    timedelta(hours=6),
]


async def create_webhook_delivery(
    db: AsyncSession,
    webhook_id: str,
    event: str,
    payload: dict,
) -> WebhookDelivery:
    delivery = WebhookDelivery(
        webhook_id=webhook_id,
        event=event,
        payload=payload,
        status="pending",
        attempt=0,
    )
    db.add(delivery)
    await db.flush()
    await db.refresh(delivery)
    return delivery


async def get_deliveries(
    db: AsyncSession,
    webhook_id: str,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[WebhookDelivery], int]:
    count_result = await db.execute(
        select(func.count())
        .select_from(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def deliver_webhook(
    db: AsyncSession,
    delivery_id: str,
) -> bool:
    result = await db.execute(
        select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
    )
    delivery = result.scalar_one_or_none()
    if not delivery:
        return False

    wh_result = await db.execute(select(Webhook).where(Webhook.id == delivery.webhook_id))
    webhook = wh_result.scalar_one_or_none()
    if not webhook or not webhook.is_active:
        delivery.status = "failed"
        await db.flush()
        return False

    body = json.dumps(delivery.payload).encode()
    headers = {"Content-Type": "application/json"}
    if webhook.secret:
        headers["X-Zly-Signature"] = _sign_payload(body, webhook.secret)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook.url, content=body, headers=headers)
            delivery.response_code = resp.status_code
            delivery.response_body = resp.text[:1000] if resp.text else None

            if 200 <= resp.status_code < 300:
                delivery.status = "success"
                delivery.delivered_at = datetime.now(timezone.utc)
                delivery.next_retry_at = None
                await db.flush()
                return True
            else:
                delivery.attempt += 1
                if delivery.attempt >= webhook.max_retries:
                    delivery.status = "dead"
                else:
                    delivery.status = "retrying"
                    delay_idx = min(delivery.attempt - 1, len(_RETRY_DELAYS) - 1)
                    delivery.next_retry_at = datetime.now(timezone.utc) + _RETRY_DELAYS[delay_idx]
                await db.flush()
                return False

    except Exception as exc:
        delivery.response_body = str(exc)[:1000]
        delivery.attempt += 1
        if delivery.attempt >= webhook.max_retries:
            delivery.status = "dead"
        else:
            delivery.status = "retrying"
            delay_idx = min(delivery.attempt - 1, len(_RETRY_DELAYS) - 1)
            delivery.next_retry_at = datetime.now(timezone.utc) + _RETRY_DELAYS[delay_idx]
        await db.flush()
        return False


async def schedule_retry(
    db: AsyncSession,
    delivery_id: str,
) -> bool:
    result = await db.execute(
        select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
    )
    delivery = result.scalar_one_or_none()
    if not delivery or delivery.status != "retrying":
        return False

    if delivery.next_retry_at and delivery.next_retry_at <= datetime.now(timezone.utc):
        from app.core.arq_pool import get_arq_pool
        pool = await get_arq_pool()
        await pool.enqueue_job("deliver_webhook", delivery_id=delivery_id)
        return True
    return False