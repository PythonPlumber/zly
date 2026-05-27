import hashlib
import secrets
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate


def _generate_api_key() -> tuple[str, str, str]:
    raw = "uf_" + secrets.token_hex(32)
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    prefix = raw[:8]
    return raw, key_hash, prefix


async def create_api_key(
    db: AsyncSession, data: ApiKeyCreate, user_id: str, workspace_id: str
) -> tuple[ApiKey, str]:
    raw, key_hash, prefix = _generate_api_key()
    api_key = ApiKey(
        key_hash=key_hash,
        prefix=prefix,
        name=data.name,
        permissions=data.permissions,
        workspace_id=workspace_id,
        user_id=user_id,
    )
    db.add(api_key)
    await db.flush()
    await db.refresh(api_key)
    return api_key, raw


async def list_api_keys(db: AsyncSession, workspace_id: str, page: int = 1, page_size: int = 50) -> tuple[list[ApiKey], int, bool]:
    base = select(ApiKey).where(ApiKey.workspace_id == workspace_id).order_by(ApiKey.created_at.desc())
    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    keys = list(result.scalars().all())
    has_next = (offset + page_size) < total
    return keys, total, has_next


async def revoke_api_key(db: AsyncSession, key_id: str) -> ApiKey | None:
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        return None
    key.is_active = False
    await db.flush()
    await db.refresh(key)
    return key


async def get_api_key(db: AsyncSession, key_id: str) -> ApiKey | None:
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    return result.scalar_one_or_none()


async def authenticate_api_key(db: AsyncSession, raw_key: str) -> ApiKey | None:
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
    )
    key = result.scalar_one_or_none()
    if key:
        key.last_used_at = datetime.now(timezone.utc)
        await db.flush()
    return key
