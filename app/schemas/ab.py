import random
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.link import _validate_url_scheme


class ABVariantCreate(BaseModel):
    destination_url: str
    weight: int = 50
    is_default: bool = False

    _validate_url = field_validator("destination_url")(_validate_url_scheme)


class ABVariantUpdate(BaseModel):
    destination_url: str | None = None
    weight: Optional[int] = None
    is_default: Optional[bool] = None

    _validate_url = field_validator("destination_url")(_validate_url_scheme)


class ABVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    link_id: str
    destination_url: str
    weight: int
    is_default: bool
