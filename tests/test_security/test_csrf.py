import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_csrf_cookie_set_on_get(client: AsyncClient):
    r = await client.get("/health")
    csrf_cookie = r.cookies.get("zly_csrf_token")
    assert csrf_cookie is not None
    assert len(csrf_cookie) == 64


@pytest.mark.asyncio
async def test_csrf_bypass_bearer(client: AsyncClient):
    r = await client.post(
        "/api/v1/links",
        json={"destination_url": "https://x.com", "workspace_id": "x"},
        headers={"Authorization": "Bearer some-token"},
    )
    # CSRF is bypassed for Bearer; 401 is from auth failure
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_csrf_bypass_auth_endpoint(client: AsyncClient):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "x@x.com", "password": "x"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_csrf_missing_header_returns_403(client: AsyncClient):
    slug = uuid.uuid4().hex[:8]
    r = await client.post(
        "/api/v1/workspaces",
        json={"name": "No CSRF", "slug": slug},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "CSRF token missing or invalid"


@pytest.mark.asyncio
async def test_csrf_wrong_token_returns_403(client: AsyncClient):
    slug = uuid.uuid4().hex[:8]
    r = await client.post(
        "/api/v1/workspaces",
        json={"name": "Bad CSRF", "slug": slug},
        headers={
            "X-CSRF-Token": "attacker-token",
            "Cookie": "zly_csrf_token=victim-token",
        },
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_csrf_valid_token_succeeds(client: AsyncClient):
    r = await client.get("/health")
    csrf_cookie = r.cookies.get("zly_csrf_token", "")
    assert csrf_cookie

    slug = uuid.uuid4().hex[:8]
    r = await client.post(
        "/api/v1/workspaces",
        json={"name": "CSRF Test", "slug": slug},
        headers={
            "X-CSRF-Token": csrf_cookie,
            "Cookie": f"zly_csrf_token={csrf_cookie}",
        },
    )
    assert r.status_code == 401
