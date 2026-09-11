import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_me(auth_client: AsyncClient):
    r = await auth_client.get("/api/v1/users/me")
    assert r.status_code == 200
    assert r.json()["email"].endswith("@test.com")


@pytest.mark.asyncio
async def test_update_display_name(auth_client: AsyncClient):
    r = await auth_client.patch("/api/v1/users/me", json={"display_name": "New Name"})
    assert r.status_code == 200
    assert r.json()["display_name"] == "New Name"


@pytest.mark.asyncio
async def test_change_password(auth_client: AsyncClient):
    r = await auth_client.post(
        "/api/v1/users/me/change-password",
        json={"old_password": "testpass123", "new_password": "newpass456"},
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_old(auth_client: AsyncClient):
    r = await auth_client.post(
        "/api/v1/users/me/change-password",
        json={"old_password": "wrongpass", "new_password": "newpass456"},
    )
    assert r.status_code == 403
