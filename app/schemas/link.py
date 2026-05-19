from datetime import datetime

from pydantic import BaseModel


class LinkBase(BaseModel):
    destination_url: str
    title: str | None = None
    short_code: str | None = None


class LinkCreate(LinkBase):
    workspace_id: str
    password: str | None = None
    expires_at: datetime | None = None
    activate_at: datetime | None = None


class LinkUpdate(BaseModel):
    destination_url: str | None = None
    title: str | None = None
    is_active: bool | None = None
    password: str | None = None
    expires_at: datetime | None = None
    activate_at: datetime | None = None


class LinkResponse(LinkBase):
    id: str
    short_code: str
    is_active: bool
    expires_at: datetime | None = None
    activate_at: datetime | None = None
    workspace_id: str
    user_id: str | None = None
    created_at: datetime
    click_count: int = 0

    model_config = {"from_attributes": True}


class PasswordVerifyRequest(BaseModel):
    password: str


class PasswordVerifyResponse(BaseModel):
    destination_url: str
