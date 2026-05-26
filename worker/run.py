import asyncio

from arq import create_pool
from arq.connections import RedisSettings

from app.config import settings
from app.db import get_session_factory


async def startup(ctx: dict) -> None:
    ctx["redis"] = await create_pool(RedisSettings.from_url(settings.redis_url))
    ctx["session_factory"] = get_session_factory()


async def shutdown(ctx: dict) -> None:
    await ctx["redis"].close()


async def process_click(ctx: dict, link_id: str, ip: str, user_agent: str, referrer: str, variant_id: str | None = None) -> None:
    from app.services.click_service import record_click

    async with ctx["session_factory"]() as db:
        try:
            await record_click(
                db,
                link_id=link_id,
                ip=ip,
                user_agent=user_agent,
                referrer=referrer,
                variant_id=variant_id,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def check_expiring_links_worker(ctx: dict, workspace_id: str) -> None:
    from app.services.notification_service import check_expiring_links

    async with ctx["session_factory"]() as db:
        try:
            await check_expiring_links(db, workspace_id)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


class WorkerSettings:
    functions = [process_click, check_expiring_links_worker]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_url(settings.redis_url)
    keep_result_seconds = 3600
    max_jobs = 10
    poll_delay = 0.5