import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_link(client: AsyncClient):
    response = await client.post(
        "/api/v1/links",
        json={"destination_url": "https://example.com", "title": "Test"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["destination_url"] == "https://example.com"
    assert data["title"] == "Test"
    assert len(data["short_code"]) == 7


@pytest.mark.asyncio
async def test_create_link_missing_url(client: AsyncClient):
    response = await client.post("/api/v1/links", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_links(client: AsyncClient):
    await client.post("/api/v1/links", json={"destination_url": "https://a.com"})
    await client.post("/api/v1/links", json={"destination_url": "https://b.com"})
    response = await client.get("/api/v1/links")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_link(client: AsyncClient):
    create_resp = await client.post(
        "/api/v1/links", json={"destination_url": "https://example.com"}
    )
    link_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/links/{link_id}")
    assert response.status_code == 200
    assert response.json()["destination_url"] == "https://example.com"


@pytest.mark.asyncio
async def test_get_link_not_found(client: AsyncClient):
    response = await client.get("/api/v1/links/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_link(client: AsyncClient):
    create_resp = await client.post(
        "/api/v1/links", json={"destination_url": "https://example.com"}
    )
    link_id = create_resp.json()["id"]
    response = await client.patch(
        f"/api/v1/links/{link_id}", json={"title": "Updated"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


@pytest.mark.asyncio
async def test_delete_link(client: AsyncClient):
    create_resp = await client.post(
        "/api/v1/links", json={"destination_url": "https://example.com"}
    )
    link_id = create_resp.json()["id"]
    response = await client.delete(f"/api/v1/links/{link_id}")
    assert response.status_code == 204
    get_resp = await client.get(f"/api/v1/links/{link_id}")
    assert get_resp.status_code == 404
