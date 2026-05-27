from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

from app.core.security import validate_private_url


ALLOWED_URL_SCHEMES = {"http", "https"}
DANGEROUS_SCHEMES = {"javascript", "data", "file", "vbscript"}


def _validate_url_scheme(v: str) -> str:
    parsed = urlparse(v)
    if parsed.scheme in DANGEROUS_SCHEMES:
        raise ValueError(f"URL with scheme '{parsed.scheme}' is not allowed")
    if parsed.scheme not in ALLOWED_URL_SCHEMES:
        raise ValueError(f"URL scheme must be http or https, got '{parsed.scheme}'")
    validate_private_url(v)
    return v


class LinkBase(BaseModel):
    destination_url: str
    title: str | None = None
    short_code: str | None = None

    _validate_url = field_validator("destination_url")(_validate_url_scheme)


class LinkCreate(LinkBase):
    workspace_id: str
    password: str | None = Field(None, min_length=1)
    expires_at: datetime | None = None
    activate_at: datetime | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_term: str | None = None
    utm_content: str | None = None


class LinkUpdate(BaseModel):
    destination_url: str | None = None
    title: str | None = None
    is_active: bool | None = None
    password: str | None = None
    expires_at: datetime | None = None
    activate_at: datetime | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_term: str | None = None
    utm_content: str | None = None

    _validate_url = field_validator("destination_url")(_validate_url_scheme)


class LinkResponse(LinkBase):
    id: str
    short_code: str
    destination_url: str
    title: str | None = None
    is_active: bool
    expires_at: datetime | None = None
    activate_at: datetime | None = None
    workspace_id: str
    user_id: str | None = None
    created_at: datetime
    updated_at: datetime
    click_count: int = 0
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_term: str | None = None
    utm_content: str | None = None

    model_config = {"from_attributes": True}


class BulkImportResponse(BaseModel):
    created: int
    errors: list[dict]


class PasswordVerifyRequest(BaseModel):
    password: str


class PasswordVerifyResponse(BaseModel):
    destination_url: str
