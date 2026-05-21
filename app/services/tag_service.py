from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag, link_tags
from app.schemas.tag import TagCreate, TagUpdate


async def create_tag(db: AsyncSession, workspace_id: str, data: TagCreate) -> Tag:
    tag = Tag(workspace_id=workspace_id, name=data.name, color=data.color)
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag


async def get_tags(db: AsyncSession, workspace_id: str) -> Sequence[Tag]:
    result = await db.execute(
        select(Tag).where(Tag.workspace_id == workspace_id).order_by(Tag.name)
    )
    return result.scalars().all()


async def get_tag(db: AsyncSession, tag_id: str) -> Tag | None:
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    return result.scalar_one_or_none()


async def update_tag(db: AsyncSession, tag: Tag, data: TagUpdate) -> Tag:
    for field in ("name", "color"):
        value = getattr(data, field, None)
        if value is not None:
            setattr(tag, field, value)
    await db.flush()
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, tag: Tag) -> None:
    await db.delete(tag)
    await db.flush()


async def set_link_tags(db: AsyncSession, link_id: str, tag_ids: list[str]) -> None:
    await db.execute(delete(link_tags).where(link_tags.c.link_id == link_id))
    for tid in tag_ids:
        await db.execute(link_tags.insert().values(link_id=link_id, tag_id=tid))
    await db.flush()
