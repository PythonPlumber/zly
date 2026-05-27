import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
async def test_forgot_password_existing_user(client: AsyncClient, db_session: AsyncSession):
    from uuid import uuid4
    from app.core.security import hash_password

    email = f"existing-{uuid4().hex[:8]}@test.com"
    user = User(email=email, password_hash=hash_password("testpass123"), display_name="Test")
    db_session.add(user)
    await db_session.flush()

    resp = await client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_user(client: AsyncClient):
    import uuid

    email = f"nonexistent-{uuid.uuid4().hex[:8]}@test.com"
    resp = await client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_reset_password_valid_token(client: AsyncClient, db_session: AsyncSession):
    from uuid import uuid4
    from app.core.security import hash_password

    email = f"reset-valid-{uuid4().hex[:8]}@test.com"
    user = User(email=email, password_hash=hash_password("oldpass123"), display_name="Reset User")
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)

    fp_resp = await client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert fp_resp.status_code == 200
    assert fp_resp.json() == {"status": "ok"}

    result = await db_session.execute(select(User).where(User.email == email))
    db_user = result.scalar_one()
    assert db_user.password_reset_token is not None

    rp_resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": db_user.password_reset_token, "new_password": "newpass123456"},
    )
    assert rp_resp.status_code == 200
    assert rp_resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "totally-fake-token-that-does-not-exist", "new_password": "newpass123456"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_set_password_oauth_user(client: AsyncClient, db_session: AsyncSession):
    from uuid import uuid4
    from app.core.security import create_access_token

    email = f"oauth-{uuid4().hex[:8]}@test.com"
    user = User(
        email=email,
        password_hash=None,
        oauth_provider="google",
        oauth_id=str(uuid4()),
        display_name="OAuth User",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)

    token = create_access_token({"sub": user.id})
    client.headers["Authorization"] = f"Bearer {token}"

    resp = await client.post("/api/v1/users/me/set-password", json={"new_password": "newpass123456"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "newpass123456"})
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
