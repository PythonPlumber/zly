import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_page(auth_client: AsyncClient):
    r = await auth_client.get("/dashboard")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_links_page(auth_client: AsyncClient):
    r = await auth_client.get("/dashboard/links")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_bio_page(auth_client: AsyncClient):
    r = await auth_client.get("/dashboard/bio")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_settings_page(auth_client: AsyncClient):
    r = await auth_client.get("/dashboard/settings")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_domains_page(auth_client: AsyncClient):
    r = await auth_client.get("/dashboard/domains")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_api_keys_page(auth_client: AsyncClient):
    r = await auth_client.get("/dashboard/api-keys")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_webhooks_page(auth_client: AsyncClient):
    r = await auth_client.get("/dashboard/webhooks")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_tags_page(auth_client: AsyncClient):
    r = await auth_client.get("/dashboard/tags")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
