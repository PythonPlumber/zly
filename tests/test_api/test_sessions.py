import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock


def _jti():
    import uuid
    return uuid.uuid4().hex


@pytest.mark.asyncio
async def test_list_sessions(auth_client: AsyncClient):
    resp = await auth_client.get("/api/v1/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)


@pytest.mark.asyncio
async def test_revoke_session_not_found(auth_client: AsyncClient, mock_redis: AsyncMock):
    mock_redis.hdel.side_effect = Exception()
    resp = await auth_client.delete(f"/api/v1/sessions/{_jti()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_revoke_all_sessions(auth_client: AsyncClient):
    resp = await auth_client.post("/api/v1/sessions/revoke-all")
    assert resp.status_code == 200
    data = resp.json()
    assert "revoked" in data
    assert isinstance(data["revoked"], int)
