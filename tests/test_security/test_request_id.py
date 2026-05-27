import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_request_id_header_present(client: AsyncClient):
    r = await client.get("/health")
    assert "x-request-id" in r.headers
    assert len(r.headers["x-request-id"]) == 36  # UUID


@pytest.mark.asyncio
async def test_request_id_echoes_client_header(client: AsyncClient):
    r = await client.get("/health", headers={"X-Request-ID": "my-custom-id"})
    assert r.headers.get("x-request-id") == "my-custom-id"