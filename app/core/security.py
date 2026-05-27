import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_db
from app.models.user import User


_PRIVATE_HOST_PATTERNS = [
    re.compile(r"^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$"),
    re.compile(r"^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$"),
    re.compile(r"^172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}$"),
    re.compile(r"^192\.168\.\d{1,3}\.\d{1,3}$"),
    re.compile(r"^169\.254\.\d{1,3}\.\d{1,3}$"),
    re.compile(r"^0\.0\.0\.0$"),
    re.compile(r"^localhost$", re.IGNORECASE),
    re.compile(r"^::1$"),
    re.compile(r"^[0-9a-fA-F:]+:[0-9a-fA-F:]+$"),
    re.compile(r"^$"),
]


def validate_private_url(url: str) -> str:
    host = urlparse(url).hostname
    if host and any(p.match(host) for p in _PRIVATE_HOST_PATTERNS):
        raise ValueError("URL pointing to a private or internal host is not allowed")
    return url


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(data: dict, expires_delta: timedelta | None = None, jti: str | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "access"})
    if jti:
        to_encode["jti"] = jti
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict, token_version: int = 0) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expire_days)
    to_encode.update({"exp": expire, "type": "refresh", "ver": token_version})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, check_blacklist: bool = False) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.PyJWTError:
        return None


def decode_refresh_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "refresh":
            return None
        return payload
    except jwt.PyJWTError:
        return None


security_scheme = HTTPBearer(auto_error=False)


async def _authenticate_via_api_key(db: AsyncSession, raw: str) -> User | None:
    from app.services.api_key_service import authenticate_api_key
    key = await authenticate_api_key(db, raw)
    if not key:
        return None
    result = await db.execute(select(User).where(User.id == key.user_id))
    user = result.scalar_one_or_none()
    if user and key.permissions:
        user._key_permissions = {p.strip() for p in key.permissions.split(",") if p.strip()}
    elif user:
        user._key_permissions = None
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    raw = credentials.credentials

    if raw.startswith("uf_"):
        user = await _authenticate_via_api_key(db, raw)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        return user

    payload = decode_access_token(raw)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    jti = payload.get("jti")
    if jti:
        from app.services.session_service import is_jti_blacklisted
        if await is_jti_blacklisted(jti):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_user_from_cookie(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = request.cookies.get("zly_token")
    if not token and credentials:
        token = credentials.credentials
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    if token.startswith("uf_"):
        user = await _authenticate_via_api_key(db, token)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        return user

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_key_permission(permission: str):
    async def _check(current_user: User = Depends(get_current_user)) -> User:
        perms = getattr(current_user, "_key_permissions", None)
        if perms is not None and permission not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key does not have permission '{permission}'",
            )
        return current_user
    return _check
