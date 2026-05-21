import pytest
from httpx import AsyncClient

from app.models.click import Click
from app.models.link import Link


def _slug():
    import uuid
    return uuid.uuid4().hex[:8]


@pytest.mark.asyncio
async def test_link_analytics(auth_client: AsyncClient, db_session, test_user_id: str):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "Ana WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    create_resp = await auth_client.post(
        "/api/v1/links", json={"destination_url": "https://example.com", "workspace_id": ws_id}
    )
    link_id = create_resp.json()["id"]

    link = await db_session.get(Link, link_id)
    for _ in range(3):
        db_session.add(Click(link_id=link.id, ip_hash="abc", browser="Chrome", os="Windows", device_type="desktop"))
    await db_session.flush()

    response = await auth_client.get(f"/api/v1/links/{link_id}/analytics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_clicks"] == 3
    assert len(data["browsers"]) == 1
    assert data["browsers"][0]["browser"] == "Chrome"
    assert data["browsers"][0]["count"] == 3


@pytest.mark.asyncio
async def test_workspace_analytics_summary(auth_client: AsyncClient, db_session, test_user_id: str):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "Sum WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    create_resp = await auth_client.post(
        "/api/v1/links", json={"destination_url": "https://example.com", "workspace_id": ws_id}
    )
    link_id = create_resp.json()["id"]

    link = await db_session.get(Link, link_id)
    for _ in range(2):
        db_session.add(Click(link_id=link.id, ip_hash="abc"))
    await db_session.flush()

    response = await auth_client.get(f"/api/v1/workspaces/{ws_id}/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_clicks"] == 2
    assert data["total_links"] == 1


@pytest.mark.asyncio
async def test_link_analytics_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/links/00000000-0000-0000-0000-000000000000/analytics")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_verify_password(auth_client: AsyncClient, db_session, test_user_id: str):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "PW WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    create_resp = await auth_client.post(
        "/api/v1/links", json={"destination_url": "https://secret.com", "workspace_id": ws_id, "password": "hunter2"}
    )
    link_id = create_resp.json()["id"]

    response = await auth_client.post(
        f"/api/v1/links/{link_id}/verify-password", json={"password": "hunter2"}
    )
    assert response.status_code == 200
    assert response.json()["destination_url"] == "https://secret.com"


@pytest.mark.asyncio
async def test_verify_password_wrong(auth_client: AsyncClient, db_session, test_user_id: str):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "PW2 WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    create_resp = await auth_client.post(
        "/api/v1/links", json={"destination_url": "https://secret.com", "workspace_id": ws_id, "password": "hunter2"}
    )
    link_id = create_resp.json()["id"]

    response = await auth_client.post(
        f"/api/v1/links/{link_id}/verify-password", json={"password": "wrong"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_qrcode_png(auth_client: AsyncClient, db_session, test_user_id: str):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "QR WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    create_resp = await auth_client.post(
        "/api/v1/links", json={"destination_url": "https://example.com", "workspace_id": ws_id}
    )
    link_id = create_resp.json()["id"]
    response = await auth_client.get(f"/api/v1/links/{link_id}/qrcode")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 100


@pytest.mark.asyncio
async def test_qrcode_svg(auth_client: AsyncClient, db_session, test_user_id: str):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "QR2 WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    create_resp = await auth_client.post(
        "/api/v1/links", json={"destination_url": "https://example.com", "workspace_id": ws_id}
    )
    link_id = create_resp.json()["id"]
    response = await auth_client.get(f"/api/v1/links/{link_id}/qrcode?format=svg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert b"<svg" in response.content


@pytest.mark.asyncio
async def test_qrcode_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/links/00000000-0000-0000-0000-000000000000/qrcode")
    assert response.status_code == 401
