from datetime import datetime

from pydantic import BaseModel, Field


class AgeVerificationRequest(BaseModel):
    birth_year: int = Field(gt=1900, le=2100)
    country: str = Field(default="US", min_length=2, max_length=2)


class AgeVerificationResponse(BaseModel):
    verified: bool
    age: int
    verified_at: datetime


class AgeStatusResponse(BaseModel):
    verified: bool
    verified_at: datetime | None
