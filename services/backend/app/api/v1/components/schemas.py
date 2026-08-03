import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SymbolOut(BaseModel):
    id: uuid.UUID
    name: str
    library: str
    svg_data: str
    pins: list
    meta: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateSymbolRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    library: str = Field(default="Enginex Standard", max_length=100)
    svg_data: str = ""
    pins: list = Field(default_factory=list)
    meta: dict = Field(default_factory=dict)


class FootprintOut(BaseModel):
    id: uuid.UUID
    name: str
    package_type: str
    pads: list
    courtyard: list
    silkscreen: list
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateFootprintRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    package_type: str = Field(min_length=1, max_length=100)
    pads: list = Field(default_factory=list)
    courtyard: list = Field(default_factory=list)
    silkscreen: list = Field(default_factory=list)


class ComponentOut(BaseModel):
    id: uuid.UUID
    name: str
    category: str
    manufacturer: str | None
    part_number: str
    datasheet_url: str | None
    symbol_id: uuid.UUID | None
    footprint_id: uuid.UUID | None
    meta: dict
    created_at: datetime

    model_config = {"from_attributes": True}
