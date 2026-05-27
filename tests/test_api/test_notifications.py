import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone


@pytest.mark.asyncio
async def test_check_expiring_no_links(auth_client: AsyncClient):
    import uuid
    slug = uuid.uuid4().hex[:8]
    ws = await auth_client.post("/api/v1/workspaces", json={"name": "Expiry Check", "slug": slug})
    ws_id = ws.json()["id"]
    r = await auth_client.post(f"/api/v1/workspaces/{ws_id}/links/check-expiring")
    assert r.status_code == 200
    data = r.json()
    assert data["notified"] == 0


@pytest.mark.asyncio
async def test_check_expiring_fires_webhook(
    auth_client: AsyncClient, db_session: AsyncSession
):
    import uuid
    slug = uuid.uuid4().hex[:8]
    ws = await auth_client.post("/api/v1/workspaces", json={"name": "Expiry Fire", "slug": slug})
    ws_id = ws.json()["id"]

    from app.schemas.webhook import WebhookCreate
    from app.services.webhook_service import create_webhook
    await create_webhook(
        db_session, ws_id,
        WebhookCreate(name="Test WH", url="http://192.0.2.1:1/nonexistent", events="link.expiring_soon"),
    )

    future = datetime.now(timezone.utc) + timedelta(hours=2)
    await auth_client.post(
        "/api/v1/links",
        json={"destination_url": "https://expiring.com", "title": "Expiring", "workspace_id": ws_id, "expires_at": future.isoformat()},
    )

    r = await auth_client.post(f"/api/v1/workspaces/{ws_id}/links/check-expiring?within_hours=24")
    assert r.status_code == 200
    data = r.json()
    assert data["notified"] == 1
    assert data["links"][0]["short_code"] is not None


@pytest.mark.asyncio
async def test_check_expiring_repeat_suppressed(
    auth_client: AsyncClient, db_session: AsyncSession
):
    import uuid
    slug = uuid.uuid4().hex[:8]
    ws = await auth_client.post("/api/v1/workspaces", json={"name": "Expiry Suppress", "slug": slug})
    ws_id = ws.json()["id"]

    future = datetime.now(timezone.utc) + timedelta(hours=2)
    link_resp = await auth_client.post(
        "/api/v1/links",
        json={"destination_url": "https://expiring2.com", "title": "Expiring 2", "workspace_id": ws_id, "expires_at": future.isoformat()},
    )
    link_id = link_resp.json()["id"]

    from app.models.link import Link
    from sqlalchemy import select
    result = await db_session.execute(select(Link).where(Link.id == link_id))
    link = result.scalar_one()
    link.last_notified_at = datetime.now(timezone.utc)
    await db_session.flush()

    r = await auth_client.post(f"/api/v1/workspaces/{ws_id}/links/check-expiring?within_hours=24")
    assert r.status_code == 200
    data = r.json()
    assert data["notified"] == 0
