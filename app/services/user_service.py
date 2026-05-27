from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import ChangePasswordRequest, SetPasswordRequest, UserUpdate


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user(db: AsyncSession, user: User, data: UserUpdate) -> User:
    if data.display_name is not None:
        user.display_name = data.display_name
    await db.flush()
    await db.refresh(user)
    return user


async def change_user_password(db: AsyncSession, user: User, data: ChangePasswordRequest) -> None:
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current password is incorrect")
    user.password_hash = hash_password(data.new_password)
    await db.flush()


async def set_user_password(db: AsyncSession, user: User, data: SetPasswordRequest) -> None:
    if user.password_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password already set. Use change-password instead.")
    user.password_hash = hash_password(data.new_password)
    await db.flush()
