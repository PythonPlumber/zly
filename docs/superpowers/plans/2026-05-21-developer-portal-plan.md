# Developer Portal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add API key auth middleware, bulk CSV import/export for links, and link expiry webhook notifications.

**Architecture:** Modify `get_current_user` in `security.py` to detect `uf_`-prefixed API keys. Add bulk endpoints + service functions using stdlib `csv`. Add `notification_service.py` for expiry checks, firing via existing `trigger_webhooks()`.

**Tech Stack:** FastAPI, SQLAlchemy, Python stdlib `csv`, asyncio

---

### Task 1: Add API key auth middleware to `get_current_user`

**Files:**
- Modify: `app/core/security.py`
- Test: `tests/test_api/test_api_keys.py`

- [ ] **Step 1: Write failing tests for API key auth**

Add to `tests/test_api/test_api_keys.py`:
```python
@pytest.mark.asyncio
async def test_authenticate_via_api_key(auth_client: AsyncClient, db_session: AsyncSession, test_workspace_id: str):
    from app.schemas.api_key import ApiKeyCreate
    from app.services.api_key_service import create_api_key
    from app.core.security import get_current_user
    key, raw = await create_api_key(
        db_session, ApiKeyCreate(name="Test Key"), "test_user_id", test_workspace_id
    )
    assert raw.startswith("uf_")
    r = await auth_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {raw}"})
    assert r.status_code == 200
    assert "email" in r.json()


@pytest.mark.asyncio
async def test_authenticate_invalid_api_key(client: AsyncClient):
    r = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer uf_invalidkey123"})
    assert r.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_api/test_api_keys.py::test_authenticate_via_api_key tests/test_api/test_api_keys.py::test_authenticate_invalid_api_key -v`
Expected: FAIL (API key not accepted)

- [ ] **Step 3: Modify `get_current_user` in security.py**

Replace the existing `get_current_user` function in `app/core/security.py`:
```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    raw = credentials.credentials

    # API key authentication
    if raw.startswith("uf_"):
        from app.services.api_key_service import authenticate_api_key
        key = await authenticate_api_key(db, raw)
        if not key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        result = await db.execute(select(User).where(User.id == key.user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user

    # JWT authentication
    payload = decode_access_token(raw)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
```

Also update `get_current_user_from_cookie` — after falling back to Bearer header (line 88-89), add the same `uf_` check before JWT decode:
```python
    token = request.cookies.get("zly_token")
    if not token and credentials:
        token = credentials.credentials
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    if token.startswith("uf_"):
        from app.services.api_key_service import authenticate_api_key
        key = await authenticate_api_key(db, token)
        if not key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        result = await db.execute(select(User).where(User.id == key.user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user

    payload = decode_access_token(token)
    # ... rest unchanged
```

- [ ] **Step 4: Fix the test — create a proper user for the API key**

The test needs a real user_id. Update the test to use `test_user_id` fixture:
```python
@pytest.mark.asyncio
async def test_authenticate_via_api_key(client: AsyncClient, db_session: AsyncSession, test_workspace_id: str, test_user_id: str):
    from app.schemas.api_key import ApiKeyCreate
    from app.services.api_key_service import create_api_key
    key, raw = await create_api_key(
        db_session, ApiKeyCreate(name="Test Key"), test_user_id, test_workspace_id
    )
    assert raw.startswith("uf_")
    r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {raw}"})
    assert r.status_code == 200
    assert "email" in r.json()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_api/test_api_keys.py -v`
Expected: all 4 tests pass (2 existing + 2 new)

- [ ] **Step 6: Commit**

```bash
git add app/core/security.py tests/test_api/test_api_keys.py
git commit -m "feat: add API key auth middleware to get_current_user"
```

---

### Task 2: Add bulk import/export endpoints

**Files:**
- Modify: `app/services/link_service.py`
- Modify: `app/schemas/link.py`
- Create: `app/api/bulk.py`
- Modify: `app/api/router.py`
- Create: `tests/test_api/test_bulk.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_api/test_bulk.py`:
```python
import io
import csv
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_bulk_import_csv(auth_client: AsyncClient, test_workspace_id: str):
    csv_content = "destination_url,title,short_code\nhttps://a.com,Link A,a\nhttps://b.com,Link B,b\nhttps://c.com,Link C,c"
    r = await auth_client.post(
        f"/api/v1/workspaces/{test_workspace_id}/links/bulk-import",
        files={"file": ("links.csv", csv_content, "text/csv")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["created"] == 3
    assert data["errors"] == []


@pytest.mark.asyncio
async def test_export_csv(auth_client: AsyncClient, test_workspace_id: str, db_session: AsyncSession, test_user_id: str):
    from app.schemas.link import LinkCreate
    from app.services.link_service import create_link
    await create_link(db_session, LinkCreate(destination_url="https://export-test.com", title="Export Me", workspace_id=test_workspace_id), test_user_id)
    r = await auth_client.get(f"/api/v1/workspaces/{test_workspace_id}/links/export")
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    reader = csv.DictReader(io.StringIO(r.text))
    rows = list(reader)
    assert len(rows) >= 1
    assert any("export-test.com" in row["destination_url"] for row in rows)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_api/test_bulk.py -v`
Expected: FAIL — 404 Not Found

- [ ] **Step 3: Add `BulkImportResponse` schema**

Add to `app/schemas/link.py`:
```python
class BulkImportResponse(BaseModel):
    created: int
    errors: list[dict]
```

- [ ] **Step 4: Add service functions to `link_service.py`**

Add at the end of `app/services/link_service.py`:
```python
import csv
from io import StringIO


async def get_links_all(db: AsyncSession, workspace_id: str) -> list[Link]:
    result = await db.execute(
        select(Link)
        .where(Link.workspace_id == workspace_id)
        .order_by(Link.created_at.desc())
    )
    return list(result.scalars().all())


async def bulk_create_links(
    db: AsyncSession,
    rows: list[dict],
    workspace_id: str,
    user_id: str | None = None,
) -> dict:
    created = 0
    errors = []
    for i, row in enumerate(rows):
        try:
            data = LinkCreate(
                destination_url=row["destination_url"],
                title=row.get("title") or None,
                short_code=row.get("short_code") or None,
                password=row.get("password") or None,
                workspace_id=workspace_id,
            )
            link = Link(
                short_code=data.short_code or generate_short_code(),
                destination_url=data.destination_url,
                title=data.title,
                workspace_id=workspace_id,
                user_id=user_id,
                password_hash=hash_password(data.password) if data.password else None,
            )
            db.add(link)
            await db.flush()
            created += 1
        except Exception as e:
            errors.append({"row": i, "error": str(e)})
    return {"created": created, "errors": errors}


async def export_links_csv(db: AsyncSession, workspace_id: str) -> str:
    links = await get_links_all(db, workspace_id)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["short_code", "destination_url", "title", "is_active", "expires_at", "created_at"])
    for link in links:
        writer.writerow([
            link.short_code, link.destination_url, link.title or "",
            str(link.is_active), str(link.expires_at or ""), str(link.created_at),
        ])
    return output.getvalue()
```

- [ ] **Step 4b: Add `hash_password` import to link_service.py**

At the top of `app/services/link_service.py`, the import for `hash_password` is already there:
```python
from app.core.security import hash_password
```

- [ ] **Step 5: Create `app/api/bulk.py`**

```python
import csv
from io import StringIO

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.link import BulkImportResponse
from app.services.link_service import bulk_create_links, export_links_csv
from app.services.workspace_service import verify_workspace_access

router = APIRouter()


@router.post("/workspaces/{workspace_id}/links/bulk-import")
async def api_bulk_import(
    workspace_id: str,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    content = await file.read()
    reader = csv.DictReader(StringIO(content.decode()))
    rows = list(reader)
    result = await bulk_create_links(db, rows, workspace_id, current_user.id)
    return result


@router.get("/workspaces/{workspace_id}/links/export")
async def api_export_links(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    csv_content = await export_links_csv(db, workspace_id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=zly-links-{workspace_id}.csv"},
    )
```

- [ ] **Step 6: Include bulk router in `app/api/router.py`**

Add after the imports and before the redirect_router:
```python
api_router.include_router(bulk.router, tags=["bulk"])
```

Add the import at the top:
```python
from app.api import bulk
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python -m pytest tests/test_api/test_bulk.py -v`
Expected: both tests pass

- [ ] **Step 8: Commit**

```bash
git add app/services/link_service.py app/schemas/link.py app/api/bulk.py app/api/router.py tests/test_api/test_bulk.py
git commit -m "feat: add bulk CSV import/export for links"
```

---

### Task 3: Add link expiry notifications via webhooks

**Files:**
- Modify: `app/models/link.py`
- Create: `app/services/notification_service.py`
- Modify: `app/api/bulk.py` (add check-expiring endpoint)
- Modify: `app/api/redirect.py` (fire-and-forget expiry check)
- Create: `tests/test_api/test_notifications.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_api/test_notifications.py`:
```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone


@pytest.mark.asyncio
async def test_check_expiring_no_links(auth_client: AsyncClient, test_workspace_id: str):
    r = await auth_client.post(f"/api/v1/workspaces/{test_workspace_id}/links/check-expiring")
    assert r.status_code == 200
    data = r.json()
    assert data["notified"] == 0


@pytest.mark.asyncio
async def test_check_expiring_fires_webhook(
    auth_client: AsyncClient, db_session: AsyncSession, test_workspace_id: str, test_user_id: str
):
    from app.schemas.link import LinkCreate
    from app.schemas.webhook import WebhookCreate
    from app.services.link_service import create_link
    from app.services.webhook_service import create_webhook

    await create_webhook(
        db_session, test_workspace_id,
        WebhookCreate(name="Test WH", url="https://httpbin.org/post", events="link.expiring_soon"),
    )
    future = datetime.now(timezone.utc) + timedelta(hours=2)
    await create_link(
        db_session,
        LinkCreate(destination_url="https://expiring.com", workspace_id=test_workspace_id, expires_at=future),
        test_user_id,
    )
    r = await auth_client.post(f"/api/v1/workspaces/{test_workspace_id}/links/check-expiring?within_hours=24")
    assert r.status_code == 200
    data = r.json()
    assert data["notified"] == 1
    assert data["links"][0]["short_code"] is not None


@pytest.mark.asyncio
async def test_check_expiring_repeat_suppressed(
    auth_client: AsyncClient, db_session: AsyncSession, test_workspace_id: str, test_user_id: str
):
    from app.schemas.link import LinkCreate
    from app.services.link_service import create_link

    future = datetime.now(timezone.utc) + timedelta(hours=2)
    link = await create_link(
        db_session,
        LinkCreate(destination_url="https://expiring2.com", workspace_id=test_workspace_id, expires_at=future),
        test_user_id,
    )
    link.last_notified_at = datetime.now(timezone.utc)
    await db_session.flush()

    r = await auth_client.post(f"/api/v1/workspaces/{test_workspace_id}/links/check-expiring?within_hours=24")
    assert r.status_code == 200
    data = r.json()
    assert data["notified"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_api/test_notifications.py -v`
Expected: FAIL — 404 Not Found for check-expiring endpoint

- [ ] **Step 3: Add `last_notified_at` to Link model**

In `app/models/link.py`, add after `activate_at`:
```python
last_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
```

- [ ] **Step 4: Create `app/services/notification_service.py`**

```python
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.services.webhook_service import trigger_webhooks


async def check_expiring_links(
    db: AsyncSession, workspace_id: str, within_hours: int = 24
) -> list[dict]:
    cutoff = datetime.now(timezone.utc) + timedelta(hours=within_hours)
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Link).where(
            Link.workspace_id == workspace_id,
            Link.expires_at.isnot(None),
            Link.expires_at <= cutoff,
            Link.expires_at > now,
            Link.is_active == True,
        )
    )
    links = result.scalars().all()
    fired = []
    for link in links:
        if link.last_notified_at and link.last_notified_at >= now - timedelta(hours=within_hours):
            continue
        payload = {
            "event": "link.expiring_soon",
            "link_id": link.id,
            "short_code": link.short_code,
            "title": link.title,
            "destination_url": link.destination_url,
            "expires_at": str(link.expires_at),
        }
        await trigger_webhooks(db, workspace_id, "link.expiring_soon", payload)
        link.last_notified_at = now
        fired.append(payload)
    await db.flush()
    return fired
```

- [ ] **Step 5: Add check-expiring endpoint to `app/api/bulk.py`**

Add before the router definition, import `Query`:
```python
from fastapi import APIRouter, Depends, Query, UploadFile
```

Add after export endpoint:
```python
@router.post("/workspaces/{workspace_id}/links/check-expiring")
async def api_check_expiring(
    workspace_id: str,
    within_hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
    from app.services.notification_service import check_expiring_links
    result = await check_expiring_links(db, workspace_id, within_hours)
    return {"notified": len(result), "links": result}
```

- [ ] **Step 6: Add fire-and-forget expiry check in redirect**

In `app/api/redirect.py`, import at the top:
```python
from app.services.notification_service import check_expiring_links
```

After the click recording block (after line ~101, after `await db_session.commit()`), add:
```python
            # Fire-and-forget expiry check
            asyncio.ensure_future(_check_expiry_on_redirect(
                link.workspace_id, link.short_code,
            ))
```

Also need to import `asyncio` at the top of redirect.py.

The helper function can go in the same file or in the existing async task section. Actually, looking at the code, there's already `_fire_webhooks` as a fire-and-forget pattern. Let me add a similar pattern.

Add at the bottom of `redirect.py`:
```python
async def _check_expiry_on_redirect(workspace_id: str, short_code: str) -> None:
    from app.db import get_session_factory
    async with get_session_factory()() as db:
        try:
            await check_expiring_links(db, workspace_id)
        except Exception:
            pass
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python -m pytest tests/test_api/test_notifications.py -v`
Expected: all 3 tests pass

- [ ] **Step 8: Run the full test suite**

Run: `python -m pytest tests/ -v --tb=no`
Expected: all tests pass (should be ~150 tests)

- [ ] **Step 9: Commit**

```bash
git add app/models/link.py app/services/notification_service.py app/api/bulk.py app/api/redirect.py tests/test_api/test_notifications.py
git commit -m "feat: add link expiry notifications via webhooks"
```
