import random
import uuid

from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ab import ABVariant
from app.schemas.ab import ABVariantCreate, ABVariantUpdate


async def create_variant(db: AsyncSession, link_id: str, data: ABVariantCreate) -> ABVariant:
    variant = ABVariant(
        id=str(uuid.uuid4()),
        link_id=link_id,
        destination_url=data.destination_url,
        weight=data.weight,
        is_default=data.is_default,
    )
    db.add(variant)
    await db.commit()
    await db.refresh(variant)
    return variant


async def get_variant(db: AsyncSession, variant_id: str) -> ABVariant | None:
    result = await db.execute(select(ABVariant).where(ABVariant.id == variant_id))
    return result.scalar_one_or_none()


async def list_variants(db: AsyncSession, link_id: str, page: int = 1, page_size: int = 50) -> tuple[list[ABVariant], int, bool]:
    base = select(ABVariant).where(ABVariant.link_id == link_id).order_by(ABVariant.weight.desc())
    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    variants = list(result.scalars().all())
    has_next = (offset + page_size) < total
    return variants, total, has_next


async def update_variant(db: AsyncSession, variant_id: str, data: ABVariantUpdate) -> ABVariant | None:
    variant = await get_variant(db, variant_id)
    if not variant:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(variant, key, value)
    await db.commit()
    await db.refresh(variant)
    return variant


async def delete_variant(db: AsyncSession, variant_id: str) -> bool:
    variant = await get_variant(db, variant_id)
    if not variant:
        return False
    await db.delete(variant)
    await db.commit()
    return True


def select_variant(variants: list[ABVariant]) -> ABVariant | None:
    if not variants:
        return None
    total_weight = sum(v.weight for v in variants)
    if total_weight == 0:
        return variants[0]
    roll = random.randint(0, total_weight - 1)
    cumulative = 0
    for v in variants:
        cumulative += v.weight
        if roll < cumulative:
            return v
    return variants[-1]
