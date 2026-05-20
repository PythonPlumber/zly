import uuid

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bio import BioPage, BioLink
from app.schemas.bio import BioPageCreate, BioPageUpdate, BioLinkCreate, BioLinkUpdate


async def create_bio_page(db: AsyncSession, workspace_id: str, data: BioPageCreate) -> BioPage:
    bio = BioPage(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        slug=data.slug,
        title=data.title,
        bio=data.bio,
        avatar_url=data.avatar_url,
        theme=data.theme,
    )
    db.add(bio)
    await db.commit()
    return await _get_bio_page(db, BioPage.id == bio.id)


async def _get_bio_page(db: AsyncSession, *filters) -> BioPage | None:
    result = await db.execute(
        select(BioPage).options(selectinload(BioPage.links)).where(*filters)
    )
    return result.scalar_one_or_none()


async def get_bio_page(db: AsyncSession, workspace_id: str) -> BioPage | None:
    return await _get_bio_page(db, BioPage.workspace_id == workspace_id)


async def get_bio_page_by_slug(db: AsyncSession, slug: str) -> BioPage | None:
    return await _get_bio_page(db, BioPage.slug == slug, BioPage.is_published == True)


async def update_bio_page(db: AsyncSession, workspace_id: str, data: BioPageUpdate) -> BioPage | None:
    bio = await get_bio_page(db, workspace_id)
    if not bio:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(bio, key, value)
    await db.commit()
    return await _get_bio_page(db, BioPage.id == bio.id)


async def delete_bio_page(db: AsyncSession, workspace_id: str) -> bool:
    bio = await get_bio_page(db, workspace_id)
    if not bio:
        return False
    await db.delete(bio)
    await db.commit()
    return True


async def add_bio_link(db: AsyncSession, bio_page_id: str, data: BioLinkCreate) -> BioLink:
    link = BioLink(
        id=str(uuid.uuid4()),
        bio_page_id=bio_page_id,
        link_id=data.link_id,
        title=data.title,
        url=data.url,
        position=data.position,
        is_active=data.is_active,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


async def update_bio_link(db: AsyncSession, link_id: str, data: BioLinkUpdate) -> BioLink | None:
    result = await db.execute(select(BioLink).where(BioLink.id == link_id))
    bio_link = result.scalar_one_or_none()
    if not bio_link:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(bio_link, key, value)
    await db.commit()
    await db.refresh(bio_link)
    return bio_link


async def remove_bio_link(db: AsyncSession, link_id: str) -> bool:
    result = await db.execute(select(BioLink).where(BioLink.id == link_id))
    bio_link = result.scalar_one_or_none()
    if not bio_link:
        return False
    await db.delete(bio_link)
    await db.commit()
    return True


async def reorder_bio_links(db: AsyncSession, bio_page_id: str, link_ids: list[str]) -> list[BioLink]:
    links = []
    for i, link_id in enumerate(link_ids):
        result = await db.execute(
            select(BioLink).where(BioLink.id == link_id, BioLink.bio_page_id == bio_page_id)
        )
        bio_link = result.scalar_one_or_none()
        if bio_link:
            bio_link.position = i
            links.append(bio_link)
    await db.commit()
    for link in links:
        await db.refresh(link)
    return sorted(links, key=lambda l: l.position)
