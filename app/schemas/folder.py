from datetime import datetime

from pydantic import BaseModel


class FolderCreate(BaseModel):
    name: str


class FolderResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
