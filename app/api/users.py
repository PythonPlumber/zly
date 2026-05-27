from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import ChangePasswordRequest, SetPasswordRequest, UserResponse, UserUpdate
from app.services.user_service import change_user_password, set_user_password, update_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def api_get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def api_update_me(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await update_user(db, current_user, data)


@router.post("/me/change-password")
async def api_change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await change_user_password(db, current_user, data)
    return {"status": "ok"}


@router.post("/me/set-password")
async def api_set_password(
    data: SetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await set_user_password(db, current_user, data)
    return {"status": "ok"}
