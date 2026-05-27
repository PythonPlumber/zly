import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.domain import CustomDomain
from app.schemas.domain import DomainCreate


def generate_verification_code() -> str:
    return f"{settings.domain_verify_prefix}={uuid.uuid4().hex}"


async def create_domain(db: AsyncSession, workspace_id: str, data: DomainCreate) -> CustomDomain:
    existing = await get_domain_by_name(db, data.domain)
    if existing:
        return None

    domain = CustomDomain(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        domain=data.domain,
        verification_code=generate_verification_code(),
    )
    db.add(domain)
    await db.commit()
    await db.refresh(domain)
    return domain


async def get_domain_by_name(db: AsyncSession, domain: str) -> CustomDomain | None:
    result = await db.execute(
        select(CustomDomain).where(CustomDomain.domain == domain)
    )
    return result.scalar_one_or_none()


async def get_domain(db: AsyncSession, domain_id: str) -> CustomDomain | None:
    result = await db.execute(select(CustomDomain).where(CustomDomain.id == domain_id))
    return result.scalar_one_or_none()


async def list_workspace_domains(db: AsyncSession, workspace_id: str, page: int = 1, page_size: int = 50) -> tuple[list[CustomDomain], int, bool]:
    base = select(CustomDomain).where(CustomDomain.workspace_id == workspace_id).order_by(CustomDomain.created_at)
    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    domains = list(result.scalars().all())
    has_next = (offset + page_size) < total
    return domains, total, has_next


async def verify_domain(db: AsyncSession, domain_id: str, verification_code: str) -> CustomDomain | None:
    domain = await get_domain(db, domain_id)
    if not domain:
        return None
    if domain.verification_code != verification_code:
        return None
    domain.is_verified = True
    await db.commit()
    await db.refresh(domain)
    return domain


async def delete_domain(db: AsyncSession, domain_id: str) -> bool:
    domain = await get_domain(db, domain_id)
    if not domain:
        return False
    await db.delete(domain)
    await db.commit()
    return True


async def get_workspace_by_domain(db: AsyncSession, domain: str) -> str | None:
    result = await db.execute(
        select(CustomDomain).where(CustomDomain.domain == domain, CustomDomain.is_verified == True)
    )
    custom_domain = result.scalar_one_or_none()
    if custom_domain:
        return custom_domain.workspace_id
    return None
