import uuid
from datetime import datetime

from pydantic import BaseModel


class PlanFeatures(BaseModel):
    projects_limit: int | None
    storage_gb: int | None
    ai_suggestions: bool
    collaboration_users: int | None
    export_formats: list[str] | str
    cad_features: list[str] | str
    pcb_features: list[str] | str
    simulation: bool | str


class PlanPricing(BaseModel):
    tier: str
    price_monthly: float | None
    price_annual: float | None
    is_custom: bool
    features: PlanFeatures


class PricingResponse(BaseModel):
    plans: list[PlanPricing]


class CreateCheckoutRequest(BaseModel):
    organization_id: uuid.UUID
    plan_tier: str
    billing_cycle: str = "monthly"


class CheckoutResponse(BaseModel):
    status: str
    checkout_url: str | None = None
    contact_sales: bool = False
    message: str | None = None


class SubscriptionOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    tier: str
    status: str
    billing_cycle: str | None
    current_period_end: datetime | None

    model_config = {"from_attributes": True}
