import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_tag(auth_client: AsyncClient, db_session):
    ws_r = await auth_client.post("/api/v1/workspaces", json={"name": "TagWS", "slug": "tagws"})
    ws_id = ws_r.json()["id"]

    r = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/tags",
        json={"name": "important", "color": "#ff0000"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "important"
    assert data["color"] == "#ff0000"


@pytest.mark.asyncio
async def test_list_tags(auth_client: AsyncClient):
    ws_r = await auth_client.post("/api/v1/workspaces", json={"name": "ListT", "slug": "listt"})
    ws_id = ws_r.json()["id"]

    await auth_client.post(f"/api/v1/workspaces/{ws_id}/tags", json={"name": "tag1"})
    r = await auth_client.get(f"/api/v1/workspaces/{ws_id}/tags")
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_update_tag(auth_client: AsyncClient):
    ws_r = await auth_client.post("/api/v1/workspaces", json={"name": "UpdT", "slug": "updt"})
    ws_id = ws_r.json()["id"]

    created = await auth_client.post(f"/api/v1/workspaces/{ws_id}/tags", json={"name": "old-name"})
    tag_id = created.json()["id"]
    r = await auth_client.patch(
        f"/api/v1/tags/{tag_id}",
        json={"name": "new-name", "color": "#00ff00"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "new-name"
    assert r.json()["color"] == "#00ff00"


@pytest.mark.asyncio
async def test_delete_tag(auth_client: AsyncClient):
    ws_r = await auth_client.post("/api/v1/workspaces", json={"name": "DelT", "slug": "delt"})
    ws_id = ws_r.json()["id"]

    created = await auth_client.post(f"/api/v1/workspaces/{ws_id}/tags", json={"name": "delete-me"})
    tag_id = created.json()["id"]
    r = await auth_client.delete(f"/api/v1/tags/{tag_id}")
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_set_link_tags(auth_client: AsyncClient):
    ws_r = await auth_client.post("/api/v1/workspaces", json={"name": "LinkT", "slug": "linkt"})
    ws_id = ws_r.json()["id"]

    link_r = await auth_client.post(
        "/api/v1/links",
        json={"destination_url": "https://example.com", "workspace_id": ws_id},
    )
    link_id = link_r.json()["id"]

    t1 = await auth_client.post(f"/api/v1/workspaces/{ws_id}/tags", json={"name": "a"})
    t2 = await auth_client.post(f"/api/v1/workspaces/{ws_id}/tags", json={"name": "b"})
    r = await auth_client.post(
        f"/api/v1/links/{link_id}/tags",
        json={"tag_ids": [t1.json()["id"], t2.json()["id"]]},
    )
    assert r.status_code == 204

    link_get = await auth_client.get(f"/api/v1/links/{link_id}")
    assert link_get.status_code == 200
