import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_page_renders(client: AsyncClient):
    r = await client.get("/login")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_register_page_renders(client: AsyncClient):
    r = await client.get("/register")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_logout_clears_cookie(client: AsyncClient):
    r = await client.post("/logout")
    assert r.status_code == 303 or r.status_code == 302
    set_cookie = r.headers.get("set-cookie", "")
    assert "zly_token=;" in set_cookie or "Max-Age=0" in set_cookie
