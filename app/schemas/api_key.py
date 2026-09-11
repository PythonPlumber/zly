from datetime import datetime

from pydantic import BaseModel, Field


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    permissions: str | None = Field(None, description="Comma-separated list of permissions (empty = all)")


class ApiKeyResponse(BaseModel):
    id: str
    prefix: str
    name: str
    workspace_id: str
    permissions: str | None = None
    is_active: bool
    last_used_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyWithRaw(ApiKeyResponse):
    raw_key: str

    model_config = {"from_attributes": True}


class ApiKeyUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None
