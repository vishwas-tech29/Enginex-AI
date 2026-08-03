import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CreateSimulationJobRequest(BaseModel):
    project_id: uuid.UUID
    file_id: uuid.UUID | None = None
    job_type: str = Field(min_length=1, max_length=50)
    parameters: dict = Field(default_factory=dict)


class SimulationJobOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    file_id: uuid.UUID | None
    job_type: str
    status: str
    parameters: dict
    result: dict | None
    report_url: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
