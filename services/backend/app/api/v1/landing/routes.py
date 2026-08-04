import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.v1.billing.schemas import PricingResponse
from app.api.v1.billing.service import BillingService
from app.api.v1.landing.analytics_service import AnalyticsService
from app.api.v1.landing.schemas import SignupRequest, SignupResponse, TrackEventRequest
from app.api.v1.landing.service import LandingService
from app.database import get_db
from app.utils.security import decode_token

router = APIRouter(prefix="/landing", tags=["Landing"])


def _optional_user_id(request: Request) -> uuid.UUID | None:
    """Best-effort: attribute an analytics event to a logged-in user if a
    valid bearer token is present, without requiring one (this endpoint is
    hit by anonymous landing-page visitors too)."""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return None
    try:
        payload = decode_token(auth_header.split(" ", 1)[1])
        return uuid.UUID(payload["sub"])
    except Exception:
        return None


@router.get("/pricing", response_model=PricingResponse)
def get_pricing(db: Session = Depends(get_db)):
    return {"plans": BillingService(db).get_pricing()}


@router.post("/signup", response_model=SignupResponse, status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    return LandingService(db).signup(payload)


@router.post("/analytics/event", status_code=202)
def track_event(payload: TrackEventRequest, request: Request, db: Session = Depends(get_db)):
    AnalyticsService(db).track(
        event_name=payload.event,
        user_id=_optional_user_id(request),
        properties=payload.properties,
        url=payload.url,
        user_agent=request.headers.get("user-agent"),
    )
    return {"status": "ok"}
