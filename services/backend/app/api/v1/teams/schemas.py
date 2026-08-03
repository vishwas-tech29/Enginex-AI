import uuid

from pydantic import BaseModel, Field


class UpdateTeamRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class AddTeamMemberRequest(BaseModel):
    user_id: uuid.UUID
    role: str = Field(default="member", pattern="^(lead|member)$")


class TeamOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    members: list

    model_config = {"from_attributes": True}
