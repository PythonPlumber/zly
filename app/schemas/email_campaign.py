from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class EmailContactCreate(BaseModel):
    email: EmailStr


class EmailContactResponse(BaseModel):
    id: str
    workspace_id: str
    email: str
    status: str
    unsubscribed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailTemplateCreate(BaseModel):
    name: str = Field(..., max_length=100)
    subject: str = Field(..., max_length=200)
    html_body: str
    is_default: bool = False


class EmailTemplateUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    subject: str | None = Field(None, max_length=200)
    html_body: str | None = None
    is_default: bool | None = None


class EmailTemplateResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    subject: str
    html_body: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmailCampaignCreate(BaseModel):
    name: str = Field(..., max_length=100)
    subject: str = Field(..., max_length=200)
    html_body: str
    from_email: EmailStr | None = None
    from_name: str | None = Field(None, max_length=100)
    scheduled_at: datetime | None = None


class EmailCampaignUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    subject: str | None = Field(None, max_length=200)
    html_body: str | None = None
    from_email: str | None = None
    from_name: str | None = None
    status: str | None = None


class EmailCampaignResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    subject: str
    html_body: str
    status: str
    from_email: str | None = None
    from_name: str | None = None
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    stats: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmailCampaignStatsResponse(BaseModel):
    sent: int = 0
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    bounced: int = 0
    unsubscribed: int = 0