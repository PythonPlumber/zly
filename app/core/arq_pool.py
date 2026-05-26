from arq import create_pool
from arq.connections import RedisSettings

from app.config import settings

_pool = None


async def get_arq_pool():
    global _pool
    if _pool is None:
        _pool = await create_pool(RedisSettings.from_url(settings.redis_url))
    return _pool


async def close_arq_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
