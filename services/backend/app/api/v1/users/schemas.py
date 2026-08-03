import uuid

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    avatar: str | None = None
    settings: dict = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    avatar: str | None = None
    settings: dict | None = None
