import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CreateBoardRequest(BaseModel):
    file_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    width_mm: float = 0
    height_mm: float = 0
    layers_count: int = Field(default=2, ge=1)


class UpdateBoardRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    width_mm: float | None = None
    height_mm: float | None = None
    layers_count: int | None = Field(default=None, ge=1)
    data: dict | None = None


class BoardOut(BaseModel):
    id: uuid.UUID
    file_id: uuid.UUID
    name: str
    width_mm: float
    height_mm: float
    layers_count: int
    data: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateComponentRequest(BaseModel):
    board_id: uuid.UUID
    reference_designator: str = Field(min_length=1, max_length=50)
    footprint_id: uuid.UUID | None = None
    library_entry_id: uuid.UUID | None = None
    position_x: float = 0
    position_y: float = 0
    rotation_degrees: float = 0
    data: dict = Field(default_factory=dict)


class UpdateComponentRequest(BaseModel):
    reference_designator: str | None = Field(default=None, min_length=1, max_length=50)
    position_x: float | None = None
    position_y: float | None = None
    rotation_degrees: float | None = None
    data: dict | None = None


class ComponentOut(BaseModel):
    id: uuid.UUID
    board_id: uuid.UUID
    reference_designator: str
    footprint_id: uuid.UUID | None
    library_entry_id: uuid.UUID | None
    position_x: float
    position_y: float
    rotation_degrees: float
    data: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
