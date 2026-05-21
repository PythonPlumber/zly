from datetime import datetime

from pydantic import BaseModel


class InviteCreate(BaseModel):
    email: str
    role: str = "member"


class InviteResponse(BaseModel):
    id: str
    workspace_id: str
    invited_by_user_id: str
    email: str
    role: str
    status: str
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


class MemberResponse(BaseModel):
    user_id: str
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}
