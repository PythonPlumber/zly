import hashlib
import hmac
import json
from collections.abc import Sequence

import httpx
from sqlalchemy import select
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


async def get_webhooks(db: AsyncSession, workspace_id: str) -> Sequence[Webhook]:
    result = await db.execute(
        select(Webhook).where(Webhook.workspace_id == workspace_id).order_by(Webhook.created_at.desc())
    )
    return result.scalars().all()


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
    body = json.dumps(payload).encode()

    for wh in webhooks:
        if not wh.has_event(event):
            continue
        headers = {"Content-Type": "application/json"}
        if wh.secret:
            headers["X-Zly-Signature"] = _sign_payload(body, wh.secret)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(wh.url, content=body, headers=headers)
                results.append({"webhook_id": wh.id, "status": resp.status_code})
        except Exception as e:
            results.append({"webhook_id": wh.id, "status": 0, "error": str(e)})

    return results
