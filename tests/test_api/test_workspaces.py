import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_workspace(auth_client: AsyncClient):
    response = await auth_client.post(
        "/api/v1/workspaces",
        json={"name": "My Workspace"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Workspace"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_workspaces(auth_client: AsyncClient):
    await auth_client.post("/api/v1/workspaces", json={"name": "WS 1"})
    await auth_client.post("/api/v1/workspaces", json={"name": "WS 2"})
    response = await auth_client.get("/api/v1/workspaces")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 3


@pytest.mark.asyncio
async def test_get_workspace(auth_client: AsyncClient):
    create_resp = await auth_client.post("/api/v1/workspaces", json={"name": "My WS"})
    ws_id = create_resp.json()["id"]
    response = await auth_client.get(f"/api/v1/workspaces/{ws_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "My WS"


@pytest.mark.asyncio
async def test_delete_workspace(auth_client: AsyncClient):
    create_resp = await auth_client.post("/api/v1/workspaces", json={"name": "Delete Me"})
    ws_id = create_resp.json()["id"]
    response = await auth_client.delete(f"/api/v1/workspaces/{ws_id}")
    assert response.status_code == 204
