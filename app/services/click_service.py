import hashlib

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.user_agent import extract_domain, parse_user_agent
from app.models.click import Click


async def record_click(
    db: AsyncSession,
    link_id: str,
    ip: str,
    user_agent: str | None,
    referrer: str | None,
    variant_id: str | None = None,
    country: str | None = None,
    city: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> Click:
    parsed = parse_user_agent(user_agent)
    click = Click(
        link_id=link_id,
        ip_hash=hashlib.sha256(ip.encode()).hexdigest(),
        user_agent=user_agent,
        referrer=referrer,
        referrer_domain=extract_domain(referrer),
        browser=parsed["browser"],
        browser_version=parsed["browser_version"],
        os=parsed["os"],
        device_type=parsed["device_type"],
        variant_id=variant_id,
        country=country,
        city=city,
        latitude=latitude,
        longitude=longitude,
    )
    db.add(click)
    await db.flush()
    return click