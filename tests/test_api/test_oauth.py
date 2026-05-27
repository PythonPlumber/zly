import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_google_login_url(client: AsyncClient):
    r = await client.get("/api/v1/auth/oauth/google/login")
    assert r.status_code == 200
    data = r.json()
    assert "url" in data
    assert data["url"].startswith("https://accounts.google.com/")


@pytest.mark.asyncio
async def test_github_login_url(client: AsyncClient):
    r = await client.get("/api/v1/auth/oauth/github/login")
    assert r.status_code == 200
    data = r.json()
    assert "url" in data
    assert data["url"].startswith("https://github.com/")


@pytest.mark.asyncio
async def test_oauth_callback_invalid_state(client: AsyncClient):
    r = await client.get("/api/v1/auth/oauth/callback", params={"code": "abc", "state": "invalid"})
    assert r.status_code == 400
    assert "Invalid or expired state parameter" in r.json()["detail"]


@pytest.mark.asyncio
async def test_oauth_callback_missing_params(client: AsyncClient):
    r = await client.get("/api/v1/auth/oauth/callback")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_set_password_already_set(auth_client: AsyncClient):
    r = await auth_client.post(
        "/api/v1/users/me/set-password",
        json={"new_password": "newpass12345678"},
    )
    assert r.status_code == 400
    assert "Password already set" in r.json()["detail"]
