from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.billing.schemas import CheckoutResponse, CreateCheckoutRequest
from app.api.v1.billing.service import BillingService
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout(
    payload: CreateCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BillingService(db).create_checkout_session(
        payload.organization_id, payload.plan_tier, payload.billing_cycle, current_user
    )


@router.post("/webhook", status_code=200)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    BillingService(db).handle_webhook(payload, sig_header)
    return {"received": True}
