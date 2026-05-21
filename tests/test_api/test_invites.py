import pytest
from httpx import AsyncClient


def _slug():
    import uuid
    return uuid.uuid4().hex[:8]


@pytest.mark.asyncio
async def test_create_invite(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "Inv WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    response = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/invites",
        json={"email": "invited@test.com", "role": "member"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "invited@test.com"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_invites(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "LI WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    await auth_client.post(f"/api/v1/workspaces/{ws_id}/invites", json={"email": "a@test.com"})
    await auth_client.post(f"/api/v1/workspaces/{ws_id}/invites", json={"email": "b@test.com"})
    response = await auth_client.get(f"/api/v1/workspaces/{ws_id}/invites")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_cancel_invite(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "CI WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    create_resp = await auth_client.post(f"/api/v1/workspaces/{ws_id}/invites", json={"email": "cancel@test.com"})
    invite_id = create_resp.json()["id"]
    response = await auth_client.delete(f"/api/v1/workspaces/{ws_id}/invites/{invite_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_list_members(auth_client: AsyncClient, db_session, test_user_id: str):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "LM WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    response = await auth_client.get(f"/api/v1/workspaces/{ws_id}/members")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["role"] == "owner"


@pytest.mark.asyncio
async def test_accept_invite_endpoint(auth_client: AsyncClient, db_session, test_user_id: str):
    from app.models.user import User
    from sqlalchemy import select

    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "Acc WS", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    from app.services.invite_service import create_invite
    invite = await create_invite(db_session, ws_id, test_user_id, "acceptep@test.com", "member")
    token = invite.token
    db_session.add(invite)
    await db_session.flush()

    from app.core.security import hash_password
    user = User(email="acceptep@test.com", password_hash=hash_password("pass"), display_name="Accept EP")
    db_session.add(user)
    await db_session.flush()

    response = await auth_client.post(f"/api/v1/workspaces/{ws_id}/invites/accept?token={token}")
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
