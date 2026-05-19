from redis.asyncio import ConnectionPool, Redis

from app.config import settings

pool: ConnectionPool | None = None


async def get_redis() -> Redis:
    global pool
    if pool is None:
        pool = ConnectionPool.from_url(settings.redis_url, decode_responses=True)
    return Redis(connection_pool=pool)


async def close_redis() -> None:
    global pool
    if pool:
        await pool.disconnect()
        pool = None
