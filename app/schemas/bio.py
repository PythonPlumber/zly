import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BioLinkCreate(BaseModel):
    link_id: str
    title: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., min_length=1)
    position: int = 0
    is_active: bool = True


class BioLinkUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    url: Optional[str] = None
    position: Optional[int] = None
    is_active: Optional[bool] = None


class BioLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    bio_page_id: str
    link_id: str
    title: str
    url: str
    position: int
    is_active: bool
    created_at: datetime


class BioPageCreate(BaseModel):
    slug: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$")
    title: str = Field(..., min_length=1, max_length=100)
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    theme: str = "midnight"


class BioPageUpdate(BaseModel):
    slug: Optional[str] = None
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    theme: Optional[str] = None
    is_published: Optional[bool] = None


class BioPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    slug: str
    title: str
    bio: Optional[str]
    avatar_url: Optional[str]
    theme: str
    is_published: bool
    created_at: datetime
    updated_at: datetime
    links: list[BioLinkResponse] = []


class BioPagePublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    bio: Optional[str]
    avatar_url: Optional[str]
    theme: str
    links: list[BioLinkResponse] = []
