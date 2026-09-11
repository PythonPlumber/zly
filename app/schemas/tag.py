from datetime import datetime

from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9 _-]+$")
    color: str | None = "#6366f1"


class TagUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9 _-]+$")
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
