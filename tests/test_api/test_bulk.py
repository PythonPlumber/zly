import csv
import io

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


def _slug():
    import uuid
    return uuid.uuid4().hex[:8]


@pytest.mark.asyncio
async def test_bulk_import_csv(auth_client: AsyncClient):
    ws = await auth_client.post("/api/v1/workspaces", json={"name": "Bulk Import", "slug": _slug()})
    ws_id = ws.json()["id"]
    csv_content = "destination_url,title,short_code\nhttps://a.com,Link A,ab\nhttps://b.com,Link B,bc\nhttps://c.com,Link C,cd"
    r = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/links/bulk-import",
        files={"file": ("links.csv", csv_content, "text/csv")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["created"] == 3
    assert data["errors"] == []


@pytest.mark.asyncio
async def test_bulk_import_file_too_large(auth_client: AsyncClient):
    from app.config import settings
    original = settings.max_upload_size_mb
    settings.max_upload_size_mb = 0
    try:
        ws = await auth_client.post("/api/v1/workspaces", json={"name": "Bulk Size", "slug": _slug()})
        ws_id = ws.json()["id"]
        r = await auth_client.post(
            f"/api/v1/workspaces/{ws_id}/links/bulk-import",
            files={"file": ("big.csv", "a,b,c\nd,e,f", "text/csv")},
        )
        assert r.status_code == 413
        assert "too large" in r.json()["detail"].lower()
    finally:
        settings.max_upload_size_mb = original


@pytest.mark.asyncio
async def test_export_csv(auth_client: AsyncClient):
    ws = await auth_client.post("/api/v1/workspaces", json={"name": "Bulk Export", "slug": _slug()})
    ws_id = ws.json()["id"]
    await auth_client.post(
        "/api/v1/links",
        json={"destination_url": "https://export-test.com", "title": "Export Me", "workspace_id": ws_id},
    )
    r = await auth_client.get(f"/api/v1/workspaces/{ws_id}/links/export")
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    reader = csv.DictReader(io.StringIO(r.text))
    rows = list(reader)
    assert len(rows) >= 1
    assert any("export-test.com" in row["destination_url"] for row in rows)
