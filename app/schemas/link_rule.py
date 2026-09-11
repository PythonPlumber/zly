from datetime import datetime

from pydantic import BaseModel, field_validator


class LinkRuleCreate(BaseModel):
    type: str  # geo | device | os | language | referrer
    match_value: str
    destination_url: str
    priority: int = 0

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"geo", "device", "os", "language", "referrer", "country", "city"}
        if v not in allowed:
            raise ValueError(f"type must be one of {allowed}")
        return v


class LinkRuleResponse(BaseModel):
    id: str
    link_id: str
    type: str
    match_value: str
    destination_url: str
    priority: int
    created_at: datetime

    model_config = {"from_attributes": True}
