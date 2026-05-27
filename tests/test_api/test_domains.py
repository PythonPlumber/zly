import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_add_domain(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"dom-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Dom WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    response = await client.post(
        f"/api/v1/workspaces/{ws_id}/domains",
        json={"domain": "links.example.com"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["domain"] == "links.example.com"
    assert data["is_verified"] is False
    assert data["verification_code"].startswith("zly-verify=")


@pytest.mark.asyncio
async def test_add_duplicate_domain(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"dom-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Dup Dom WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    await client.post(
        f"/api/v1/workspaces/{ws_id}/domains",
        json={"domain": "dup.example.com"},
        headers=headers,
    )
    response = await client.post(
        f"/api/v1/workspaces/{ws_id}/domains",
        json={"domain": "dup.example.com"},
        headers=headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_domains(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"dom-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "List Dom WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    await client.post(
        f"/api/v1/workspaces/{ws_id}/domains",
        json={"domain": "a.example.com"},
        headers=headers,
    )
    await client.post(
        f"/api/v1/workspaces/{ws_id}/domains",
        json={"domain": "b.example.com"},
        headers=headers,
    )
    response = await client.get(f"/api/v1/workspaces/{ws_id}/domains", headers=headers)
    assert response.status_code == 200
    data = response.json()["items"]
    assert len(data) == 2


@pytest.mark.asyncio
async def test_verify_domain(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"dom-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Verify Dom WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    add_resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/domains",
        json={"domain": "verify.example.com"},
        headers=headers,
    )
    domain_id = add_resp.json()["id"]
    verification_code = add_resp.json()["verification_code"]

    response = await client.post(
        f"/api/v1/workspaces/{ws_id}/domains/{domain_id}/verify",
        json={"verification_code": verification_code},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["is_verified"] is True


@pytest.mark.asyncio
async def test_verify_domain_wrong_code(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"dom-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Wrong WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    add_resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/domains",
        json={"domain": "wrong.example.com"},
        headers=headers,
    )
    domain_id = add_resp.json()["id"]

    response = await client.post(
        f"/api/v1/workspaces/{ws_id}/domains/{domain_id}/verify",
        json={"verification_code": "wrong-code"},
        headers=headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_domain(client: AsyncClient, db_session: AsyncSession):
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from app.core.security import create_access_token

    email = f"dom-{uuid.uuid4().hex[:8]}@test.com"
    user = await register_user(db_session, RegisterRequest(email=email, password="testpass"))
    token = create_access_token({"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Del Dom WS", "slug": uuid.uuid4().hex[:8]},
        headers=headers,
    )
    ws_id = ws_resp.json()["id"]

    add_resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/domains",
        json={"domain": "del.example.com"},
        headers=headers,
    )
    domain_id = add_resp.json()["id"]

    response = await client.delete(
        f"/api/v1/workspaces/{ws_id}/domains/{domain_id}",
        headers=headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_domain_requires_auth(client: AsyncClient, db_session: AsyncSession):
    from app.models.workspace import Workspace
    from app.models.user import User
    from app.services.auth_service import hash_password

    user = User(email=f"dom-auth-{uuid.uuid4().hex[:8]}@test.com", password_hash=hash_password("pass"))
    db_session.add(user)
    await db_session.flush()
    ws = Workspace(name="Auth Dom WS", slug=f"auth-dom-{uuid.uuid4().hex[:8]}", owner_id=user.id)
    db_session.add(ws)
    await db_session.flush()

    response = await client.get(f"/api/v1/workspaces/{ws.id}/domains")
    assert response.status_code == 401
