import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


def _slug():
    import uuid
    return uuid.uuid4().hex[:8]


@pytest.mark.asyncio
async def test_create_api_key(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "API Key WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    response = await auth_client.post(f"/api/v1/workspaces/{ws_id}/api-keys", json={"name": "My Key"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Key"
    assert data["prefix"] == data["raw_key"][:8]
    assert "raw_key" in data


@pytest.mark.asyncio
async def test_revoke_api_key(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "Revoke WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    create_resp = await auth_client.post(f"/api/v1/workspaces/{ws_id}/api-keys", json={"name": "Kill Me"})
    key_id = create_resp.json()["id"]
    response = await auth_client.delete(f"/api/v1/workspaces/{ws_id}/api-keys/{key_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_authenticate_via_api_key(
    client: AsyncClient, db_session: AsyncSession, test_workspace_id: str, test_user_id: str
):
    from app.schemas.api_key import ApiKeyCreate
    from app.services.api_key_service import create_api_key
    key, raw = await create_api_key(
        db_session, ApiKeyCreate(name="Auth Key"), test_user_id, test_workspace_id
    )
    assert raw.startswith("uf_")
    r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {raw}"})
    assert r.status_code == 200
    assert "email" in r.json()


@pytest.mark.asyncio
async def test_authenticate_invalid_api_key(client: AsyncClient):
    r = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer uf_invalidkey123"})
    assert r.status_code == 401
