import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CreateOrganizationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class UpdateOrganizationRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    settings: dict | None = None


class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    subscription_tier: str
    settings: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateTeamRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class TeamOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    members: list

    model_config = {"from_attributes": True}
