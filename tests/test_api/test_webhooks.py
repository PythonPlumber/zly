import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_webhook(auth_client: AsyncClient):
    ws_r = await auth_client.post("/api/v1/workspaces", json={"name": "WHWS", "slug": "whws"})
    ws_id = ws_r.json()["id"]

    r = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/webhooks",
        json={"name": "Test Hook", "url": "https://example.com/hook", "events": "click.created"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Test Hook"
    assert data["url"] == "https://example.com/hook"
    assert data["events"] == "click.created"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_webhooks(auth_client: AsyncClient):
    ws_r = await auth_client.post("/api/v1/workspaces", json={"name": "WHL", "slug": "whl"})
    ws_id = ws_r.json()["id"]

    await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/webhooks",
        json={"name": "Hook 1", "url": "https://ex.com/1", "events": "click.created"},
    )
    r = await auth_client.get(f"/api/v1/workspaces/{ws_id}/webhooks")
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_webhook(auth_client: AsyncClient):
    ws_r = await auth_client.post("/api/v1/workspaces", json={"name": "WHG", "slug": "whg"})
    ws_id = ws_r.json()["id"]

    created = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/webhooks",
        json={"name": "Get Hook", "url": "https://ex.com/get", "events": "click.created"},
    )
    wh_id = created.json()["id"]
    r = await auth_client.get(f"/api/v1/workspaces/{ws_id}/webhooks/{wh_id}")
    assert r.status_code == 200
    assert r.json()["name"] == "Get Hook"


@pytest.mark.asyncio
async def test_update_webhook(auth_client: AsyncClient):
    ws_r = await auth_client.post("/api/v1/workspaces", json={"name": "WHU", "slug": "whu"})
    ws_id = ws_r.json()["id"]

    created = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/webhooks",
        json={"name": "Old Name", "url": "https://ex.com/old", "events": "click.created"},
    )
    wh_id = created.json()["id"]
    r = await auth_client.patch(
        f"/api/v1/workspaces/{ws_id}/webhooks/{wh_id}",
        json={"name": "New Name", "is_active": False},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "New Name"
    assert r.json()["is_active"] is False


@pytest.mark.asyncio
async def test_delete_webhook(auth_client: AsyncClient):
    ws_r = await auth_client.post("/api/v1/workspaces", json={"name": "WHD", "slug": "whd"})
    ws_id = ws_r.json()["id"]

    created = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/webhooks",
        json={"name": "Delete Me", "url": "https://ex.com/del", "events": "click.created"},
    )
    wh_id = created.json()["id"]
    r = await auth_client.delete(f"/api/v1/workspaces/{ws_id}/webhooks/{wh_id}")
    assert r.status_code == 204
