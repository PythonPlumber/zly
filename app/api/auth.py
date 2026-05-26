from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.core.logging import get_logger
logger = get_logger(__name__)
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    create_password_reset_token,
    create_tokens,
    refresh_user_token,
    register_user,
    reset_password_with_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def api_register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    response: Response = None,
):
    try:
        user = await register_user(db, data)
        logger.info("User registered", extra={"user_id": user.id, "email": user.email})
        access, refresh = await create_tokens(user)
        response.set_cookie(
            key="zly_token",
            value=access,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=settings.jwt_expire_minutes * 60,
            path="/",
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def api_login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
    response: Response = None,
):
    user = await authenticate_user(db, data.email, data.password)
    if not user:
        logger.warning("Login failed", extra={"email": data.email})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    logger.info("User logged in", extra={"user_id": user.id, "email": user.email})
    access, refresh = await create_tokens(user)
    token_data = TokenResponse(access_token=access, refresh_token=refresh)
    response.set_cookie(
        key="zly_token",
        value=token_data.access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )
    return token_data


@router.post("/refresh", response_model=TokenResponse)
async def api_refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await refresh_user_token(data.refresh_token, db=db)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    access, refresh = result
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=UserResponse)
async def api_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password")
async def api_forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await create_password_reset_token(db, data.email)
    if not user:
        return {"status": "ok"}
    email_data = {
        "user_id": user.id,
        "to_email": user.email,
        "reset_url": f"{settings.default_domain}/auth/reset-password?token={user.password_reset_token}",
        "expires_at": user.password_reset_expires_at.strftime("%Y-%m-%d %H:%M UTC"),
    }
    try:
        from app.core.arq_pool import get_arq_pool
        pool = await get_arq_pool()
        await pool.enqueue_job("send_password_reset_email_job", **email_data)
    except Exception as exc:
        logger.warning("Failed to enqueue password reset email, skipping", extra={"user_id": user.id, "error": str(exc)})
    return {"status": "ok"}


@router.post("/reset-password")
async def api_reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await reset_password_with_token(db, data.token, data.new_password)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    logger.info("Password reset successful", extra={"user_id": user.id})
    return {"status": "ok"}
