import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CreateProjectRequest(BaseModel):
    organization_id: uuid.UUID
    team_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    type: str = Field(default="mixed", pattern="^(cad|pcb|mixed|robotics)$")


class UpdateProjectRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = Field(default=None, pattern="^(active|archived)$")


class ProjectOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    team_id: uuid.UUID | None
    name: str
    description: str | None
    owner_id: uuid.UUID
    type: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShareProjectRequest(BaseModel):
    user_id: uuid.UUID
    role: str = Field(default="viewer", pattern="^(owner|editor|viewer)$")


class InviteProjectRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="viewer", pattern="^(owner|editor|viewer)$")


class ProjectMemberOut(BaseModel):
    user_id: uuid.UUID
    email: str
    name: str
    role: str
