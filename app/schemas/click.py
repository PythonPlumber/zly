from datetime import datetime

from pydantic import BaseModel


class ClickResponse(BaseModel):
    id: int
    link_id: str
    timestamp: datetime
    ip_hash: str | None = None
    country: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    user_agent: str | None = None
    browser: str | None = None
    browser_version: str | None = None
    os: str | None = None
    device_type: str | None = None
    referrer: str | None = None
    referrer_domain: str | None = None
    variant_id: str | None = None

    model_config = {"from_attributes": True}
