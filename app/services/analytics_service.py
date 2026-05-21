from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.click import Click
from app.models.link import Link


async def get_total_clicks(db: AsyncSession, link_id: str) -> int:
    result = await db.execute(
        select(func.count(Click.id)).where(Click.link_id == link_id)
    )
    return result.scalar() or 0


async def get_clicks_over_time(
    db: AsyncSession, link_id: str, days: int = 30
) -> list[dict]:
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
    return [{"date": str(row.date), "count": row.count} for row in result]


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
    return {
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
