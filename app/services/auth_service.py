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
from app.schemas.auth import RegisterRequest
from app.schemas.workspace import WorkspaceCreate
from app.services.workspace_service import create_workspace


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
    await db.refresh(user)

    slug = data.email.split("@")[0]
    await create_workspace(
        db,
        WorkspaceCreate(name=f"{data.display_name or slug}'s Workspace", slug=slug),
        user.id,
    )

    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def create_tokens(user: User) -> tuple[str, str]:
    access = create_access_token({"sub": user.id})
    refresh = create_refresh_token({"sub": user.id})
    return access, refresh


async def refresh_user_token(refresh_token: str) -> tuple[str, str] | None:
    payload = decode_refresh_token(refresh_token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    access = create_access_token({"sub": user_id})
    refresh = create_refresh_token({"sub": user_id})
    return access, refresh


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
