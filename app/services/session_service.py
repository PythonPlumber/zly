import json
import uuid
from datetime import datetime, timezone

from app.core.logging import get_logger

logger = get_logger(__name__)

_JTI_PREFIX = "jti:"
_SESSION_PREFIX = "sessions:"


async def _get_redis():
    from app.core.redis import get_redis
    return await get_redis()


async def blacklist_jti(jti: str, ttl: int = 86400 * 7) -> None:
    try:
        r = await _get_redis()
        await r.setex(f"{_JTI_PREFIX}{jti}", ttl, "1")
    except Exception as exc:
        logger.debug("Failed to blacklist JTI (Redis unavailable)", extra={"error": str(exc)})


async def is_jti_blacklisted(jti: str) -> bool:
    try:
        r = await _get_redis()
        return bool(await r.exists(f"{_JTI_PREFIX}{jti}"))
    except Exception:
        return False


async def record_session(user_id: str, jti: str, ip: str | None, user_agent: str | None) -> None:
    try:
        r = await _get_redis()
        session = {
            "jti": jti,
            "ip": ip or "unknown",
            "user_agent": user_agent or "unknown",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await r.hset(f"{_SESSION_PREFIX}{user_id}", jti, json.dumps(session))
        await r.expire(f"{_SESSION_PREFIX}{user_id}", 86400 * 30)
    except Exception as exc:
        logger.debug("Failed to record session (Redis unavailable)", extra={"error": str(exc)})


async def list_sessions(user_id: str, current_jti: str | None = None) -> list[dict]:
    try:
        r = await _get_redis()
        sessions = await r.hgetall(f"{_SESSION_PREFIX}{user_id}")
        result = []
        for s in sessions.values():
            data = json.loads(s)
            data["is_current"] = data.get("jti") == current_jti
            result.append(data)
        return result
    except Exception:
        return []


async def revoke_session(user_id: str, jti: str) -> bool:
    try:
        r = await _get_redis()
        await r.hdel(f"{_SESSION_PREFIX}{user_id}", jti)
        await blacklist_jti(jti)
        return True
    except Exception:
        return False


async def revoke_all_sessions(user_id: str, except_jti: str | None = None) -> int:
    sessions = await list_sessions(user_id)
    count = 0
    for s in sessions:
        jti = s.get("jti")
        if jti and jti != except_jti:
            if await revoke_session(user_id, jti):
                count += 1
    return count


def generate_jti() -> str:
    return uuid.uuid4().hex
