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
