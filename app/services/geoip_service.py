import os
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)

_reader = None


def _get_reader():
    global _reader
    if _reader is not None:
        return _reader
    db_path = os.getenv("GEOIP_DB_PATH", "")
    if not db_path:
        return None
    if not Path(db_path).exists():
        logger.warning("GeoIP database not found at %s", db_path)
        return None
    try:
        import geoip2.database
        _reader = geoip2.database.Reader(db_path)
        logger.info("GeoIP database loaded from %s", db_path)
    except ImportError:
        logger.warning("geoip2 library not installed, GeoIP resolution disabled")
    except Exception as exc:
        logger.warning("Failed to load GeoIP database: %s", exc)
    return _reader


async def resolve_ip(ip: str) -> dict:
    result = {
        "country": None,
        "city": None,
        "latitude": None,
        "longitude": None,
    }
    reader = _get_reader()
    if not reader:
        return result
    try:
        response = reader.city(ip)
        result["country"] = response.country.iso_code
        result["city"] = response.city.name
        result["latitude"] = response.location.latitude
        result["longitude"] = response.location.longitude
    except Exception:
        pass
    return result
