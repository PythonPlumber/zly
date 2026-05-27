from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import hash_password
from app.models.link import Link
from app.schemas.link import LinkCreate, LinkUpdate
from app.services.short_code import generate_short_code
from app.services.webhook_service import trigger_webhooks

logger = get_logger(__name__)


def _append_utm(url: str, data) -> str:
    utm_params = {}
    for field in ("utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"):
        val = getattr(data, field, None)
        if val:
            utm_params[field] = val
    if not utm_params:
        return url
    from urllib.parse import urlencode, urlparse, urlunparse, parse_qs, ParseResult
    parsed = urlparse(url)
    existing = parse_qs(parsed.query, keep_blank_values=True)
    existing.update(utm_params)
    new_query = urlencode(existing, doseq=True)
    return urlunparse(ParseResult(parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))


async def _invalidate_link_cache(short_code: str, link_id: str, workspace_id: str) -> None:
    try:
        from app.core.redis import get_redis
        r = await get_redis()
        await r.delete(f"link:{short_code}")
        from app.services.analytics_service import invalidate_analytics_cache
        await invalidate_analytics_cache(link_id, workspace_id)
    except Exception:
        logger.debug("Cache invalidation skipped (Redis unavailable)")


async def create_link(db: AsyncSession, data: LinkCreate, user_id: str | None = None) -> Link:
    short_code = data.short_code or generate_short_code()
    destination_url = _append_utm(data.destination_url, data)
    link = Link(
        short_code=short_code,
        destination_url=destination_url,
        title=data.title,
        workspace_id=data.workspace_id,
        user_id=user_id,
        password_hash=hash_password(data.password) if data.password else None,
        expires_at=data.expires_at,
        activate_at=data.activate_at,
    )
    db.add(link)
    await db.flush()
    payload = {
        "event": "link.created",
        "link_id": link.id,
        "short_code": link.short_code,
        "destination_url": link.destination_url,
        "workspace_id": link.workspace_id,
        "user_id": link.user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await trigger_webhooks(db, link.workspace_id, "link.created", payload)
    except Exception:
        pass
    await db.refresh(link)
    return link


async def get_link_by_code(db: AsyncSession, short_code: str) -> Link | None:
    result = await db.execute(select(Link).where(Link.short_code == short_code))
    return result.scalar_one_or_none()


async def get_link_by_id(db: AsyncSession, link_id: str) -> Link | None:
    result = await db.execute(select(Link).where(Link.id == link_id))
    return result.scalar_one_or_none()


async def get_links(
    db: AsyncSession, workspace_id: str, page: int = 1, page_size: int = 20
) -> tuple[list[Link], int, bool]:
    from sqlalchemy import func, select

    base = select(Link).where(Link.workspace_id == workspace_id).order_by(Link.created_at.desc())

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    links = list(result.scalars().all())

    has_next = (offset + page_size) < total
    return links, total, has_next


async def update_link(db: AsyncSession, link: Link, data: LinkUpdate) -> Link:
    update_data = data.model_dump(exclude_unset=True)
    utm_fields = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}
    has_new_utm = any(f in update_data for f in utm_fields)
    if has_new_utm and "destination_url" not in update_data:
        update_data["destination_url"] = link.destination_url
    if "destination_url" in update_data:
        update_data["destination_url"] = _append_utm(update_data["destination_url"], data)
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
    await _invalidate_link_cache(link.short_code, link.id, link.workspace_id)
    return link


async def delete_link(db: AsyncSession, link: Link) -> None:
    short_code = link.short_code
    link_id = link.id
    workspace_id = link.workspace_id
    payload = {
        "event": "link.deleted",
        "link_id": link.id,
        "short_code": link.short_code,
        "workspace_id": link.workspace_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await trigger_webhooks(db, link.workspace_id, "link.deleted", payload)
    except Exception:
        pass
    await db.delete(link)
    await db.flush()
    await _invalidate_link_cache(short_code, link_id, workspace_id)


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
    links = []
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
            links.append(link)
        except Exception as e:
            errors.append({"row": i, "error": str(e)})

    if errors:
        return {"created": 0, "errors": errors}

    for link in links:
        db.add(link)
    await db.flush()
    return {"created": len(links), "errors": []}


async def export_links_csv(db: AsyncSession, workspace_id: str) -> str:
    import csv
    from io import StringIO
    links = await get_links_all(db, workspace_id)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["short_code", "destination_url", "title", "is_active", "expires_at", "created_at", "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"])
    for link in links:
        writer.writerow([
            link.short_code, link.destination_url, link.title or "",
            str(link.is_active), str(link.expires_at or ""), str(link.created_at),
        ])
    return output.getvalue()
