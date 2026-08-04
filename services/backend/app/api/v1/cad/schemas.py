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


# --- Sketch geometry -------------------------------------------------------


class AddPointRequest(BaseModel):
    x: float
    y: float
    fixed: bool = False


class AddLineRequest(BaseModel):
    start_id: str
    end_id: str


class AddCircleRequest(BaseModel):
    center_id: str
    radius: float = Field(gt=0)


class AddArcRequest(BaseModel):
    center_id: str
    radius: float = Field(gt=0)
    start_angle: float
    end_angle: float


class AddSketchConstraintRequest(BaseModel):
    type: str
    entities: list[str]
    value: float | None = None


class SolveSketchResponse(BaseModel):
    status: str
    is_fully_constrained: bool
    residual_norm: float
    dof_remaining: int
    conflicting_constraints: list[str]
    message: str


# --- Bodies / features -------------------------------------------------------


class CreateBodyRequest(BaseModel):
    file_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)


class ExtrudeRequest(BaseModel):
    sketch_id: uuid.UUID
    distance: float
    symmetric: bool = False


class RevolveRequest(BaseModel):
    sketch_id: uuid.UUID
    angle: float = Field(default=360, gt=0, le=360)
    axis_point: list[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    axis_dir: list[float] = Field(default_factory=lambda: [0.0, 1.0, 0.0])


class FilletRequest(BaseModel):
    radius: float = Field(gt=0)
    selector: str | None = None


class ChamferRequest(BaseModel):
    distance: float = Field(gt=0)
    selector: str | None = None


class BooleanRequest(BaseModel):
    other_body_id: uuid.UUID


class MeshResponse(BaseModel):
    vertices: list[list[float]]
    triangles: list[list[int]]
    bounding_box: dict
    volume: float
    surface_area: float


# --- Assemblies -------------------------------------------------------


class CreateAssemblyRequest(BaseModel):
    file_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)


class AddAssemblyPartRequest(BaseModel):
    body_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    position: list[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])


class AddAssemblyConstraintRequest(BaseModel):
    type: str
    part1_instance_id: str
    part2_instance_id: str
    axis_point: list[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    axis_dir: list[float] = Field(default_factory=lambda: [0.0, 0.0, 1.0])


class AnimateConstraintRequest(BaseModel):
    parameter: float


class CollisionsResponse(BaseModel):
    collisions: list[list[str]]
