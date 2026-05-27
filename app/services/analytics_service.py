import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.click import Click
from app.models.link import Link

logger = get_logger(__name__)

_CACHE_TTL = 300  # 5 minutes


async def _cache_get(key: str):
    try:
        from app.core.redis import get_redis
        r = await get_redis()
        val = await r.get(key)
        if val:
            return json.loads(val)
    except Exception:
        pass
    return None


async def _cache_set(key: str, value, ttl: int = _CACHE_TTL):
    try:
        from app.core.redis import get_redis
        r = await get_redis()
        await r.setex(key, ttl, json.dumps(value))
    except Exception:
        pass


async def _cache_del(key: str):
    try:
        from app.core.redis import get_redis
        r = await get_redis()
        await r.delete(key)
    except Exception:
        pass


async def invalidate_analytics_cache(link_id: str, workspace_id: str | None = None) -> None:
    await _cache_del(f"analytics:link:{link_id}:total_clicks")
    await _cache_del(f"analytics:link:{link_id}:clicks_over_time")
    if workspace_id:
        await _cache_del(f"analytics:workspace:{workspace_id}:summary")


async def get_total_clicks(db: AsyncSession, link_id: str) -> int:
    cache_key = f"analytics:link:{link_id}:total_clicks"
    cached = await _cache_get(cache_key)
    if cached is not None:
        return cached
    result = await db.execute(
        select(func.count(Click.id)).where(Click.link_id == link_id)
    )
    total = result.scalar() or 0
    await _cache_set(cache_key, total)
    return total


async def get_clicks_over_time(
    db: AsyncSession, link_id: str, days: int = 30
) -> list[dict]:
    cache_key = f"analytics:link:{link_id}:clicks_over_time:{days}"
    cached = await _cache_get(cache_key)
    if cached is not None:
        return cached
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            func.date(Click.timestamp).label("date"),
            func.count(Click.id).label("count"),
        )
        .where(Click.link_id == link_id, Click.timestamp >= cutoff)
        .group_by(func.date(Click.timestamp))
        .order_by(func.date(Click.timestamp))
    )
    items = [{"date": str(row.date), "count": row.count} for row in result]
    await _cache_set(cache_key, items)
    return items


async def get_top_referrers(
    db: AsyncSession, link_id: str, limit: int = 10
) -> list[dict]:
    result = await db.execute(
        select(Click.referrer_domain, func.count(Click.id).label("count"))
        .where(
            Click.link_id == link_id,
            Click.referrer_domain.isnot(None),
            Click.referrer_domain != "",
        )
        .group_by(Click.referrer_domain)
        .order_by(func.count(Click.id).desc())
        .limit(limit)
    )
    return [{"domain": row.referrer_domain, "count": row.count} for row in result]


async def get_browser_stats(db: AsyncSession, link_id: str) -> list[dict]:
    result = await db.execute(
        select(Click.browser, func.count(Click.id).label("count"))
        .where(Click.link_id == link_id, Click.browser.isnot(None))
        .group_by(Click.browser)
        .order_by(func.count(Click.id).desc())
    )
    return [{"browser": row.browser, "count": row.count} for row in result]


async def get_device_stats(db: AsyncSession, link_id: str) -> list[dict]:
    result = await db.execute(
        select(Click.device_type, func.count(Click.id).label("count"))
        .where(Click.link_id == link_id, Click.device_type.isnot(None))
        .group_by(Click.device_type)
        .order_by(func.count(Click.id).desc())
    )
    return [{"device": row.device_type, "count": row.count} for row in result]


async def get_os_stats(db: AsyncSession, link_id: str) -> list[dict]:
    result = await db.execute(
        select(Click.os, func.count(Click.id).label("count"))
        .where(Click.link_id == link_id, Click.os.isnot(None))
        .group_by(Click.os)
        .order_by(func.count(Click.id).desc())
    )
    return [{"os": row.os, "count": row.count} for row in result]


async def get_workspace_summary(
    db: AsyncSession, workspace_id: str, days: int = 7
) -> dict:
    cache_key = f"analytics:workspace:{workspace_id}:summary:{days}"
    cached = await _cache_get(cache_key)
    if cached is not None:
        return cached
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            Link.id,
            Link.short_code,
            Link.destination_url,
            Link.title,
            func.count(Click.id).label("clicks"),
        )
        .outerjoin(Click, Click.link_id == Link.id)
        .where(Link.workspace_id == workspace_id)
        .group_by(Link.id)
        .order_by(func.count(Click.id).desc())
    )
    rows = result.all()
    summary = {
        "total_clicks": sum(r.clicks for r in rows),
        "total_links": len(rows),
        "links": [
            {
                "id": r.id,
                "short_code": r.short_code,
                "destination_url": r.destination_url,
                "title": r.title,
                "clicks": r.clicks,
            }
            for r in rows
        ],
    }
    await _cache_set(cache_key, summary)
    return summary


async def get_variant_stats(db: AsyncSession, variant_id: str) -> dict:
    from app.models.click import Click
    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count()).where(Click.variant_id == variant_id)
    )
    total = count_result.scalar() or 0
    return {"variant_id": variant_id, "clicks": total}


async def get_variant_clicks_over_time(db: AsyncSession, variant_id: str, days: int = 30) -> list[dict]:
    from app.models.click import Click
    from app.core.dependencies import get_redis_client
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            func.date(Click.timestamp).label("date"),
            func.count().label("count"),
        )
        .where(Click.variant_id == variant_id, Click.timestamp >= cutoff)
        .group_by(func.date(Click.timestamp))
        .order_by(func.date(Click.timestamp))
    )
    return [{"date": str(r.date), "clicks": r.count} for r in result]
