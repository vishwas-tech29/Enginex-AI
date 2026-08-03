import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CreateSketchRequest(BaseModel):
    file_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    data: dict = Field(default_factory=dict)


class UpdateSketchRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    data: dict | None = None


class CADObjectOut(BaseModel):
    id: uuid.UUID
    file_id: uuid.UUID
    object_type: str
    name: str
    data: dict
    parent_id: uuid.UUID | None
    version_number: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
