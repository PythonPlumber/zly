import random
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ABVariantCreate(BaseModel):
    destination_url: str = Field(..., min_length=1)
    weight: int = 50
    is_default: bool = False


class ABVariantUpdate(BaseModel):
    destination_url: Optional[str] = None
    weight: Optional[int] = None
    is_default: Optional[bool] = None


class ABVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    link_id: str
    destination_url: str
    weight: int
    is_default: bool
