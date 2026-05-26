import re
from urllib.parse import urlparse

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.link import _validate_url_scheme


PRIVATE_HOST_PATTERNS = [
    re.compile(r"^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$"),
    re.compile(r"^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$"),
    re.compile(r"^172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}$"),
    re.compile(r"^192\.168\.\d{1,3}\.\d{1,3}$"),
    re.compile(r"^169\.254\.\d{1,3}\.\d{1,3}$"),
    re.compile(r"^localhost$", re.IGNORECASE),
    re.compile(r"^::1$"),
]


def _reject_private_url(v: str) -> str:
    _validate_url_scheme(v)
    host = urlparse(v).hostname
    if host and any(p.match(host) for p in PRIVATE_HOST_PATTERNS):
        raise ValueError("Webhook URL must not point to private or internal hosts")
    return v


class WebhookCreate(BaseModel):
    name: str
    url: str
    secret: str | None = Field(None, max_length=255)
    events: str = "click.created"
    is_active: bool = True

    _validate_url = field_validator("url")(_reject_private_url)


class WebhookUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    secret: str | None = None
    events: str | None = None
    is_active: bool | None = None

    _validate_url = field_validator("url")(_reject_private_url)


class WebhookResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    url: str
    secret: str | None = None
    events: str
    is_active: bool
    max_retries: int
    created_at: datetime

    model_config = {"from_attributes": True}
