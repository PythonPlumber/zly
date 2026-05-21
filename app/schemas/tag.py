from datetime import datetime

from pydantic import BaseModel


class TagCreate(BaseModel):
    name: str
    color: str | None = "#6366f1"


class TagUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


class TagResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    color: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LinkTagRequest(BaseModel):
    tag_ids: list[str]
