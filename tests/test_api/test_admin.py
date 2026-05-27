import pytest
import pytest_asyncio
from httpx import AsyncClient


def _slug():
    import uuid
    return uuid.uuid4().hex[:8]


@pytest_asyncio.fixture
async def superuser_client(client: AsyncClient, db_session) -> AsyncClient:
    import uuid
    from app.core.security import create_access_token

    email = f"superuser-{uuid.uuid4().hex[:8]}@test.com"
    resp = await client.post("/api/v1/auth/register", json={"email": email, "password": "testpass123"})
    user_id = resp.json()["id"]

    from sqlalchemy import select
    from app.models.user import User
    result = await db_session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.is_superuser = True
    await db_session.flush()

    token = create_access_token({"sub": user.id})
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.mark.asyncio
async def test_admin_users_not_superuser(auth_client: AsyncClient):
    """Regular user should receive 403 when accessing admin endpoints."""
    response = await auth_client.get("/api/v1/admin/users")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_list_users(superuser_client: AsyncClient):
    """Superuser can list users paginated."""
    response = await superuser_client.get("/api/v1/admin/users")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert data["total"] >= 1
    assert data["page"] == 1
    assert "page_size" in data
    assert "has_next" in data
    assert len(data["items"]) >= 1
    user = data["items"][0]
    assert "id" in user
    assert "email" in user
    assert "is_superuser" in user
    assert "is_active" in user


@pytest.mark.asyncio
async def test_admin_get_user(superuser_client: AsyncClient):
    """Superuser can get a specific user by id."""
    list_resp = await superuser_client.get("/api/v1/admin/users")
    user_id = list_resp.json()["items"][0]["id"]
    response = await superuser_client.get(f"/api/v1/admin/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert "email" in data
    assert "display_name" in data
    assert "is_superuser" in data
    assert "is_active" in data


@pytest.mark.asyncio
async def test_admin_get_user_not_found(superuser_client: AsyncClient):
    """Getting a non-existent user returns 404."""
    response = await superuser_client.get("/api/v1/admin/users/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_user(superuser_client: AsyncClient, client: AsyncClient):
    """Superuser can toggle is_superuser on a user."""
    reg_resp = await client.post("/api/v1/auth/register", json={"email": f"normal-{_slug()}@test.com", "password": "testpass123"})
    target_id = reg_resp.json()["id"]

    response = await superuser_client.patch(f"/api/v1/admin/users/{target_id}", json={"is_superuser": True})
    assert response.status_code == 200
    assert response.json()["status"] == "updated"

    get_resp = await superuser_client.get(f"/api/v1/admin/users/{target_id}")
    assert get_resp.json()["is_superuser"] is True

    response = await superuser_client.patch(f"/api/v1/admin/users/{target_id}", json={"is_superuser": False})
    assert response.status_code == 200
    get_resp = await superuser_client.get(f"/api/v1/admin/users/{target_id}")
    assert get_resp.json()["is_superuser"] is False


@pytest.mark.asyncio
async def test_admin_update_user_not_found(superuser_client: AsyncClient):
    """Updating a non-existent user returns 404."""
    response = await superuser_client.patch("/api/v1/admin/users/00000000-0000-0000-0000-000000000000", json={"is_superuser": True})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_stats(superuser_client: AsyncClient):
    """Stats endpoint returns all 9 integer counts."""
    response = await superuser_client.get("/api/v1/admin/stats")
    assert response.status_code == 200
    data = response.json()
    expected_keys = {"users", "workspaces", "links", "clicks", "webhooks",
                     "workspace_members", "email_campaigns", "email_contacts", "audit_logs"}
    assert set(data.keys()) == expected_keys
    for v in data.values():
        assert isinstance(v, int)


@pytest.mark.asyncio
async def test_admin_audit_logs(superuser_client: AsyncClient):
    """Audit logs return paginated results (may be empty)."""
    response = await superuser_client.get("/api/v1/admin/audit-logs")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "has_next" in data
    assert "items" in data
    assert data["total"] >= 0
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_admin_audit_logs_filtered(superuser_client: AsyncClient):
    """Filtering audit logs by action and resource_type works."""
    response = await superuser_client.get("/api/v1/admin/audit-logs?action=link.created&resource_type=link")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert isinstance(data["items"], list)
