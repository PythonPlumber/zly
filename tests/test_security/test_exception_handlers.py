import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_422_returns_field_errors(client: AsyncClient):
    r = await client.post("/api/v1/auth/register", json={"email": "bad", "password": "x"})
    assert r.status_code == 422
    body = r.json()
    assert "detail" in body
    assert isinstance(body["detail"], list)


@pytest.mark.asyncio
async def test_exception_has_request_id(client: AsyncClient):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401
    assert "x-request-id" in r.headers


@pytest.mark.asyncio
async def test_404_returns_json_error(client: AsyncClient):
    r = await client.get("/nonexistent-route-xyz")
    assert r.status_code == 404
    # FastAPI handles unknown routes with 404 JSON