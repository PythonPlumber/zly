from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.link import Link
from app.schemas.link import LinkCreate, LinkUpdate
from app.services.short_code import generate_short_code


async def create_link(db: AsyncSession, data: LinkCreate, user_id: str | None = None) -> Link:
    short_code = data.short_code or generate_short_code()
    link = Link(
        short_code=short_code,
        destination_url=data.destination_url,
        title=data.title,
        workspace_id=data.workspace_id,
        user_id=user_id,
        password_hash=hash_password(data.password) if data.password else None,
        expires_at=data.expires_at,
        activate_at=data.activate_at,
    )
    db.add(link)
    await db.flush()
    await db.refresh(link)
    return link


async def get_link_by_code(db: AsyncSession, short_code: str) -> Link | None:
    result = await db.execute(select(Link).where(Link.short_code == short_code))
    return result.scalar_one_or_none()


async def get_link_by_id(db: AsyncSession, link_id: str) -> Link | None:
    result = await db.execute(select(Link).where(Link.id == link_id))
    return result.scalar_one_or_none()


async def get_links(
    db: AsyncSession, workspace_id: str, skip: int = 0, limit: int = 20
) -> list[Link]:
    query = (
        select(Link)
        .where(Link.workspace_id == workspace_id)
        .offset(skip)
        .limit(limit)
        .order_by(Link.created_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_link(db: AsyncSession, link: Link, data: LinkUpdate) -> Link:
    update_data = data.model_dump(exclude_unset=True)
    if "password" in update_data:
        pw = update_data.pop("password")
        if pw == "":
            link.password_hash = None
        elif pw is not None:
            link.password_hash = hash_password(pw)
    for field, value in update_data.items():
        setattr(link, field, value)
    link.updated_at = datetime.now()
    await db.flush()
    await db.refresh(link)
    return link


async def delete_link(db: AsyncSession, link: Link) -> None:
    await db.delete(link)
    await db.flush()


async def get_links_all(db: AsyncSession, workspace_id: str) -> list[Link]:
    result = await db.execute(
        select(Link)
        .where(Link.workspace_id == workspace_id)
        .order_by(Link.created_at.desc())
    )
    return list(result.scalars().all())


async def bulk_create_links(
    db: AsyncSession,
    rows: list[dict],
    workspace_id: str,
    user_id: str | None = None,
) -> dict:
    created = 0
    errors = []
    for i, row in enumerate(rows):
        try:
            data = LinkCreate(
                destination_url=row["destination_url"],
                title=row.get("title") or None,
                short_code=row.get("short_code") or None,
                password=row.get("password") or None,
                workspace_id=workspace_id,
            )
            link = Link(
                short_code=data.short_code or generate_short_code(),
                destination_url=data.destination_url,
                title=data.title,
                workspace_id=workspace_id,
                user_id=user_id,
                password_hash=hash_password(data.password) if data.password else None,
            )
            db.add(link)
            await db.flush()
            created += 1
        except Exception as e:
            errors.append({"row": i, "error": str(e)})
    return {"created": created, "errors": errors}


async def export_links_csv(db: AsyncSession, workspace_id: str) -> str:
    import csv
    from io import StringIO
    links = await get_links_all(db, workspace_id)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["short_code", "destination_url", "title", "is_active", "expires_at", "created_at"])
    for link in links:
        writer.writerow([
            link.short_code, link.destination_url, link.title or "",
            str(link.is_active), str(link.expires_at or ""), str(link.created_at),
        ])
    return output.getvalue()
