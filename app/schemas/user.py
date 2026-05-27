from pydantic import BaseModel, Field


class UserUpdate(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class SetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str | None = None
    avatar_url: str | None = None

    model_config = {"from_attributes": True}
