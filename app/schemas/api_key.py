from datetime import datetime

from pydantic import BaseModel, Field


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class ApiKeyResponse(BaseModel):
    id: str
    prefix: str
    name: str
    workspace_id: str
    is_active: bool
    last_used_at: datetime | None = None
    created_at: datetime


class ApiKeyWithRaw(ApiKeyResponse):
    raw_key: str


class ApiKeyUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None
