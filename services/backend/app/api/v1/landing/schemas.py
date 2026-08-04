import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.api.v1.auth.schemas import UserOut


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    plan_tier: str = "free"
    company: str | None = None
    referral_source: str | None = None


class SignupResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut
    organization_id: uuid.UUID
    checkout_url: str | None
    contact_sales: bool
    trial_ends: datetime | None


class TrackEventRequest(BaseModel):
    event: str = Field(min_length=1, max_length=255)
    properties: dict = Field(default_factory=dict)
    url: str | None = None
