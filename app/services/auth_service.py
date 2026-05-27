from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.auth import RegisterRequest
from app.services.session_service import generate_jti, record_session


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise ValueError("Email already registered")
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
    )
    db.add(user)
    await db.flush()

    slug = data.email.split("@")[0]
    ws = Workspace(
        name=f"{data.display_name or slug}'s Workspace",
        slug=slug,
        owner_id=user.id,
    )
    db.add(ws)
    await db.flush()
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="owner"))
    await db.flush()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def create_tokens(
    user: User,
    ip: str | None = None,
    user_agent: str | None = None,
) -> tuple[str, str]:
    jti = generate_jti()
    access = create_access_token({"sub": user.id}, jti=jti)
    refresh = create_refresh_token({"sub": user.id}, token_version=user.token_version)
    await record_session(user.id, jti, ip, user_agent)
    return access, refresh


async def refresh_user_token(
    refresh_token: str,
    db: AsyncSession | None = None,
) -> tuple[str, str] | None:
    payload = decode_refresh_token(refresh_token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    token_version = payload.get("ver", 0)

    if db is not None:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None
        if user.token_version != token_version:
            return None
        user.token_version += 1
        await db.flush()

    access = create_access_token({"sub": user_id})
    refresh = create_refresh_token({"sub": user_id}, token_version=token_version + 1 if db else token_version)
    return access, refresh


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_password_reset_token(db: AsyncSession, email: str) -> User | None:
    import secrets
    from datetime import timedelta
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return None
    user.password_reset_token = secrets.token_urlsafe(48)
    user.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.flush()
    await db.refresh(user)
    return user


async def reset_password_with_token(db: AsyncSession, token: str, new_password: str) -> User | None:
    result = await db.execute(
        select(User).where(
            User.password_reset_token == token,
            User.password_reset_expires_at > datetime.now(timezone.utc),
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        return None
    user.password_hash = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires_at = None
    await db.flush()
    return user
