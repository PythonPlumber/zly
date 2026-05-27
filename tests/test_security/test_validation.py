import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_open_redirect_rejected(auth_client: AsyncClient):
    import uuid
    slug = uuid.uuid4().hex[:8]
    ws = await auth_client.post("/api/v1/workspaces", json={"name": "URL Val WS", "slug": slug})
    ws_id = ws.json()["id"]
    r = await auth_client.post(
        "/api/v1/links",
        json={"destination_url": "javascript:alert(1)", "workspace_id": ws_id},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_webhook_ssrf_localhost_rejected(auth_client: AsyncClient):
    import uuid
    slug = uuid.uuid4().hex[:8]
    ws = await auth_client.post("/api/v1/workspaces", json={"name": "SSRF Test", "slug": slug})
    ws_id = ws.json()["id"]
    r = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/webhooks",
        json={"name": "Bad WH", "url": "http://localhost:8000/hook", "events": "click.created"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_password_min_length(client: AsyncClient):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@test.com", "password": "short"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_invalid_email(client: AsyncClient):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": "notanemail", "password": "validpass123"},
    )
    assert r.status_code == 422
