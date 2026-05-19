import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@test.com", "password": "secret123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@test.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={"email": "dup@test.com", "password": "secret123"})
    response = await client.post("/api/v1/auth/register", json={"email": "dup@test.com", "password": "secret456"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={"email": "login@test.com", "password": "secret123"})
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@test.com", "password": "secret123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={"email": "bad@test.com", "password": "secret123"})
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "bad@test.com", "password": "wrongpass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={"email": "refresh@test.com", "password": "secret123"})
    login_resp = await client.post("/api/v1/auth/login", json={"email": "refresh@test.com", "password": "secret123"})
    refresh_token = login_resp.json()["refresh_token"]
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_me(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={"email": "me@test.com", "password": "secret123"})
    login_resp = await client.post("/api/v1/auth/login", json={"email": "me@test.com", "password": "secret123"})
    token = login_resp.json()["access_token"]
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@test.com"
