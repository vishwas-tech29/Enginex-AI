import uuid
from datetime import datetime

from pydantic import BaseModel


class FileOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    folder_id: uuid.UUID | None
    name: str
    type: str
    size_bytes: int
    version_number: int
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FileVersionOut(BaseModel):
    id: uuid.UUID
    file_id: uuid.UUID
    version_number: int
    size_bytes: int
    created_by: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
