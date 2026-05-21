import asyncio

from arq import create_pool
from arq.connections import RedisSettings

from app.config import settings


async def startup(ctx: dict) -> None:
    ctx["redis"] = await create_pool(RedisSettings.from_url(settings.redis_url))


async def shutdown(ctx: dict) -> None:
    await ctx["redis"].close()


async def process_click(ctx: dict, link_id: str, ip: str, user_agent: str, referrer: str) -> None:
    """Stub — will be implemented in analytics phase."""
    pass


class WorkerSettings:
    functions = [process_click]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_url(settings.redis_url)
