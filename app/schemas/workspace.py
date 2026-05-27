from datetime import datetime

from pydantic import BaseModel


class WorkspaceCreate(BaseModel):
    name: str
    slug: str | None = None


class WorkspaceUpdate(BaseModel):
    name: str | None = None


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    slug: str
    owner_id: str
    not_found_redirect: str | None = None
    brand_color: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemberResponse(BaseModel):
    user_id: str
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class InviteRequest(BaseModel):
    email: str
    role: str = "member"
