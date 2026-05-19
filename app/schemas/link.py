from datetime import datetime

from pydantic import BaseModel


class LinkBase(BaseModel):
    destination_url: str
    title: str | None = None
    short_code: str | None = None


class LinkCreate(LinkBase):
    pass


class LinkUpdate(BaseModel):
    destination_url: str | None = None
    title: str | None = None
    is_active: bool | None = None


class LinkResponse(LinkBase):
    id: str
    short_code: str
    is_active: bool
    created_at: datetime
    click_count: int = 0

    model_config = {"from_attributes": True}
