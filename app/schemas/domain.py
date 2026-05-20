import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DomainCreate(BaseModel):
    domain: str = Field(..., min_length=3, max_length=255)


class DomainVerifyRequest(BaseModel):
    verification_code: str = Field(..., min_length=1)


class DomainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    domain: str
    verification_code: str
    is_verified: bool
    created_at: datetime
