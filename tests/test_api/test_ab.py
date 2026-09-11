import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_variant(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"ab-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "AB WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    link_resp = await client.post(
        "/api/v1/links",
        json={"destination_url": "https://example.com", "workspace_id": ws_id},
        headers=headers,
    )
    link_id = link_resp.json()["id"]

    response = await client.post(
        f"/api/v1/links/{link_id}/variants",
        json={"destination_url": "https://variant.com", "weight": 50},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["destination_url"] == "https://variant.com"
    assert data["weight"] == 50


@pytest.mark.asyncio
async def test_list_variants(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"ab-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "AB List WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    link_resp = await client.post(
        "/api/v1/links",
        json={"destination_url": "https://example.com", "workspace_id": ws_id},
        headers=headers,
    )
    link_id = link_resp.json()["id"]

    await client.post(
        f"/api/v1/links/{link_id}/variants",
        json={"destination_url": "https://a.com", "weight": 50},
        headers=headers,
    )
    await client.post(
        f"/api/v1/links/{link_id}/variants",
        json={"destination_url": "https://b.com", "weight": 50},
        headers=headers,
    )

    response = await client.get(f"/api/v1/links/{link_id}/variants", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


@pytest.mark.asyncio
async def test_update_variant(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"ab-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "AB Upd WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    link_resp = await client.post(
        "/api/v1/links",
        json={"destination_url": "https://example.com", "workspace_id": ws_id},
        headers=headers,
    )
    link_id = link_resp.json()["id"]

    create_resp = await client.post(
        f"/api/v1/links/{link_id}/variants",
        json={"destination_url": "https://original.com", "weight": 50},
        headers=headers,
    )
    v_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/links/{link_id}/variants/{v_id}",
        json={"destination_url": "https://updated.com", "weight": 80},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["destination_url"] == "https://updated.com"
    assert data["weight"] == 80


@pytest.mark.asyncio
async def test_delete_variant(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"ab-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "AB Del WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    link_resp = await client.post(
        "/api/v1/links",
        json={"destination_url": "https://example.com", "workspace_id": ws_id},
        headers=headers,
    )
    link_id = link_resp.json()["id"]

    create_resp = await client.post(
        f"/api/v1/links/{link_id}/variants",
        json={"destination_url": "https://delete.com", "weight": 50},
        headers=headers,
    )
    v_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/v1/links/{link_id}/variants/{v_id}",
        headers=headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_variant_requires_auth(client: AsyncClient, db_session: AsyncSession):
    from app.models.workspace import Workspace
    from app.models.link import Link
    from app.models.user import User
    from app.services.auth_service import hash_password

    user = User(email=f"ab-auth-{uuid.uuid4().hex[:8]}@test.com", password_hash=hash_password("pass"))
    db_session.add(user)
    await db_session.flush()
    ws = Workspace(name="Auth AB WS", slug=f"auth-ab-{uuid.uuid4().hex[:8]}", owner_id=user.id)
    db_session.add(ws)
    await db_session.flush()
    link = Link(workspace_id=ws.id, destination_url="https://example.com", short_code="ab-auth")
    db_session.add(link)
    await db_session.flush()

    response = await client.get(f"/api/v1/links/{link.id}/variants")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_variant_selection(client: AsyncClient, db_session: AsyncSession):
    from app.services.ab_service import select_variant
    from app.models.ab import ABVariant

    v1 = ABVariant(link_id="test", destination_url="https://a.com", weight=70)
    v2 = ABVariant(link_id="test", destination_url="https://b.com", weight=30)
    result = select_variant([v1, v2])
    assert result is not None
    assert result.destination_url in ("https://a.com", "https://b.com")


@pytest.mark.asyncio
async def test_variant_selection_empty(client: AsyncClient):
    from app.services.ab_service import select_variant

    assert select_variant([]) is None


@pytest.mark.asyncio
async def test_redirect_with_variant(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"ab-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "AB Redir WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    import secrets
    sc = secrets.token_hex(4)
    link_resp = await client.post(
        "/api/v1/links",
        json={"destination_url": "https://example.com", "short_code": sc, "workspace_id": ws_id},
        headers=headers,
    )
    link_id = link_resp.json()["id"]

    await client.post(
        f"/api/v1/links/{link_id}/variants",
        json={"destination_url": "https://variant-redirect.com", "weight": 100},
        headers=headers,
    )

    response = await client.get(f"/{sc}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] in ("https://example.com", "https://variant-redirect.com")
