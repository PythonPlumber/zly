import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_bio_page(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"bio-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Bio WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    response = await client.post(
        f"/api/v1/workspaces/{ws_id}/bio",
        json={"slug": "my-bio", "title": "My Bio Page"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "my-bio"
    assert data["title"] == "My Bio Page"
    assert data["is_published"] is True


@pytest.mark.asyncio
async def test_create_bio_page_duplicate(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"bio-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Dup WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    await client.post(
        f"/api/v1/workspaces/{ws_id}/bio",
        json={"slug": "dup-bio", "title": "First"},
        headers=headers,
    )
    response = await client.post(
        f"/api/v1/workspaces/{ws_id}/bio",
        json={"slug": "dup-bio-2", "title": "Second"},
        headers=headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_bio_page(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"bio-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Get Bio WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    await client.post(
        f"/api/v1/workspaces/{ws_id}/bio",
        json={"slug": "get-bio", "title": "Get Bio"},
        headers=headers,
    )
    response = await client.get(f"/api/v1/workspaces/{ws_id}/bio", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "get-bio"
    assert data["title"] == "Get Bio"


@pytest.mark.asyncio
async def test_get_bio_page_not_found(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"bio-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "NF Bio WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]
    response = await client.get(f"/api/v1/workspaces/{ws_id}/bio", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_bio_page(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"bio-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Upd WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    await client.post(
        f"/api/v1/workspaces/{ws_id}/bio",
        json={"slug": "update-bio", "title": "Original"},
        headers=headers,
    )
    response = await client.put(
        f"/api/v1/workspaces/{ws_id}/bio",
        json={"title": "Updated", "theme": "light"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    assert data["theme"] == "light"


@pytest.mark.asyncio
async def test_delete_bio_page(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"bio-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Del WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    await client.post(
        f"/api/v1/workspaces/{ws_id}/bio",
        json={"slug": "del-bio", "title": "Delete Me"},
        headers=headers,
    )
    response = await client.delete(f"/api/v1/workspaces/{ws_id}/bio", headers=headers)
    assert response.status_code == 200

    get_response = await client.get(f"/api/v1/workspaces/{ws_id}/bio", headers=headers)
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_public_bio_page(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"bio-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Pub WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    await client.post(
        f"/api/v1/workspaces/{ws_id}/bio",
        json={"slug": "public-bio", "title": "Public Page"},
        headers=headers,
    )
    response = await client.get("/api/v1/bio/public-bio")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Public Page"


@pytest.mark.asyncio
async def test_public_bio_page_not_found(client: AsyncClient):
    response = await client.get("/api/v1/bio/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_bio_link(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"bio-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Link Bio WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    from app.models.link import Link
    link = Link(
        workspace_id=ws_id,
        title="Test Link",
        destination_url="https://example.com",
        short_code="bio-test-link",
    )
    db_session.add(link)
    await db_session.flush()

    await client.post(
        f"/api/v1/workspaces/{ws_id}/bio",
        json={"slug": "bio-links", "title": "With Links"},
        headers=headers,
    )
    response = await client.post(
        f"/api/v1/workspaces/{ws_id}/bio/links",
        json={"link_id": link.id, "title": "My Link", "url": "https://example.com", "position": 0},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "My Link"
    assert data["url"] == "https://example.com"


@pytest.mark.asyncio
async def test_remove_bio_link(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"bio-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Rem Bio WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    from app.models.link import Link
    link = Link(
        workspace_id=ws_id,
        title="Remove Link",
        destination_url="https://example.com",
        short_code="bio-remove-link",
    )
    db_session.add(link)
    await db_session.flush()

    await client.post(
        f"/api/v1/workspaces/{ws_id}/bio",
        json={"slug": "bio-remove", "title": "Remove Bio"},
        headers=headers,
    )
    add_resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/bio/links",
        json={"link_id": link.id, "title": "To Remove", "url": "https://example.com", "position": 0},
        headers=headers,
    )
    link_id = add_resp.json()["id"]

    response = await client.delete(
        f"/api/v1/workspaces/{ws_id}/bio/links/{link_id}",
        headers=headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_bio_page_requires_auth(client: AsyncClient, db_session: AsyncSession):
    from app.models.workspace import Workspace
    from app.models.user import User
    from app.services.auth_service import hash_password

    user = User(email=f"bio-auth-{uuid.uuid4().hex[:8]}@test.com", password_hash=hash_password("pass"))
    db_session.add(user)
    await db_session.flush()
    ws = Workspace(name="Auth WS", slug=f"auth-ws-{uuid.uuid4().hex[:8]}", owner_id=user.id)
    db_session.add(ws)
    await db_session.flush()

    response = await client.get(f"/api/v1/workspaces/{ws.id}/bio")
    assert response.status_code == 401
