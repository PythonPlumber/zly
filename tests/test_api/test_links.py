import pytest
from httpx import AsyncClient


def _slug():
    import uuid
    return uuid.uuid4().hex[:8]


@pytest.mark.asyncio
async def test_create_link(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "Link WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    response = await auth_client.post(
        "/api/v1/links",
        json={"destination_url": "https://example.com", "title": "Test", "workspace_id": ws_id},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["destination_url"] == "https://example.com"
    assert data["title"] == "Test"
    assert len(data["short_code"]) == 7


@pytest.mark.asyncio
async def test_list_links(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "List WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    await auth_client.post("/api/v1/links", json={"destination_url": "https://a.com", "workspace_id": ws_id})
    await auth_client.post("/api/v1/links", json={"destination_url": "https://b.com", "workspace_id": ws_id})
    response = await auth_client.get(f"/api/v1/links?workspace_id={ws_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["has_next"] is False


@pytest.mark.asyncio
async def test_get_link(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "Get WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    create_resp = await auth_client.post(
        "/api/v1/links", json={"destination_url": "https://example.com", "workspace_id": ws_id}
    )
    link_id = create_resp.json()["id"]
    response = await auth_client.get(f"/api/v1/links/{link_id}")
    assert response.status_code == 200
    assert response.json()["destination_url"] == "https://example.com"


@pytest.mark.asyncio
async def test_get_link_not_found(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "NF WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    await auth_client.post("/api/v1/links", json={"destination_url": "https://example.com", "workspace_id": ws_id})
    response = await auth_client.get("/api/v1/links/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_link(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "Upd WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    create_resp = await auth_client.post(
        "/api/v1/links", json={"destination_url": "https://example.com", "workspace_id": ws_id}
    )
    link_id = create_resp.json()["id"]
    response = await auth_client.patch(
        f"/api/v1/links/{link_id}", json={"title": "Updated"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


@pytest.mark.asyncio
async def test_delete_link(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "Del WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    create_resp = await auth_client.post(
        "/api/v1/links", json={"destination_url": "https://example.com", "workspace_id": ws_id}
    )
    link_id = create_resp.json()["id"]
    response = await auth_client.delete(f"/api/v1/links/{link_id}")
    assert response.status_code == 204
    get_resp = await auth_client.get(f"/api/v1/links/{link_id}")
    assert get_resp.status_code == 404
