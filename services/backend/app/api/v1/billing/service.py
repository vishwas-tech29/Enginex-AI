import logging
import uuid
from datetime import datetime, timezone

import stripe
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import NotFoundError, ServiceUnavailableError, ValidationError
from app.email.service import email_service
from app.models.organization import Organization
from app.models.subscription import Subscription
from app.models.user import User

# Feature gating per tier. "free" is this app's default (Organization.subscription_tier
# defaults to it); hobbyist/professional/enterprise are Velorah's paid tiers.
PLAN_FEATURES: dict[str, dict] = {
    "free": {
        "projects_limit": 1,
        "storage_gb": 1,
        "ai_suggestions": False,
        "collaboration_users": 1,
        "export_formats": ["STL"],
        "cad_features": ["sketch", "extrude"],
        "pcb_features": [],
        "simulation": False,
    },
    "hobbyist": {
        "projects_limit": 5,
        "storage_gb": 5,
        "ai_suggestions": True,
        "collaboration_users": 1,
        "export_formats": ["STEP", "STL", "OBJ"],
        "cad_features": ["sketch", "extrude", "revolve"],
        "pcb_features": ["placement"],
        "simulation": False,
    },
    "professional": {
        "projects_limit": None,
        "storage_gb": 500,
        "ai_suggestions": True,
        "collaboration_users": 10,
        "export_formats": ["STEP", "STL", "OBJ", "IGES", "DXF", "Gerber", "NC"],
        "cad_features": ["sketch", "extrude", "revolve", "assembly", "fillet", "chamfer"],
        "pcb_features": ["placement", "routing", "drc", "erc"],
        "simulation": True,
    },
    "enterprise": {
        "projects_limit": None,
        "storage_gb": None,
        "ai_suggestions": True,
        "collaboration_users": None,
        "export_formats": "all",
        "cad_features": "all",
        "pcb_features": "all",
        "simulation": "all",
    },
}

PLAN_PRICES: dict[str, dict[str, float | None]] = {
    "free": {"monthly": 0, "annual": 0},
    "hobbyist": {"monthly": 29, "annual": 290},
    "professional": {"monthly": 99, "annual": 990},
    "enterprise": {"monthly": None, "annual": None},
}

PAID_TIERS = ("hobbyist", "professional")

logger = logging.getLogger("enginex.billing")

# Stripe uses American spelling ("canceled"); this app's subscription_status
# enum (see migrations/versions/001_initial_schema.py) uses "cancelled".
# Map Stripe's statuses onto ours rather than writing Stripe's spelling
# straight into a column a real Postgres ENUM would reject.
_STRIPE_STATUS_MAP = {
    "active": "active",
    "trialing": "active",
    "past_due": "past_due",
    "unpaid": "past_due",
    "incomplete": "past_due",
    "canceled": "cancelled",
    "incomplete_expired": "cancelled",
}


def _stripe_price_id(plan_tier: str, billing_cycle: str) -> str | None:
    return getattr(settings, f"stripe_price_{plan_tier}_{billing_cycle}", None)


class BillingService:
    def __init__(self, db: Session):
        self.db = db

    def get_pricing(self) -> list[dict]:
        return [
            {
                "tier": tier,
                "price_monthly": PLAN_PRICES[tier]["monthly"],
                "price_annual": PLAN_PRICES[tier]["annual"],
                "is_custom": tier == "enterprise",
                "features": PLAN_FEATURES[tier],
            }
            for tier in ("free", "hobbyist", "professional", "enterprise")
        ]

    def create_checkout_session(
        self, organization_id: uuid.UUID, plan_tier: str, billing_cycle: str, user: User
    ) -> dict:
        if plan_tier not in PLAN_FEATURES:
            raise ValidationError("plan_tier", f"Unknown plan '{plan_tier}'")
        if plan_tier == "enterprise":
            return {
                "status": "pending",
                "checkout_url": None,
                "contact_sales": True,
                "message": "Enterprise plan requires sales team review",
            }
        if plan_tier == "free":
            raise ValidationError("plan_tier", "The free plan doesn't require checkout")

        org = self.db.get(Organization, organization_id)
        if not org or org.owner_id != user.id:
            raise NotFoundError("Organization", organization_id)

        if not settings.stripe_secret_key:
            raise ServiceUnavailableError(
                "Billing is not configured on this server yet (STRIPE_SECRET_KEY unset)"
            )

        price_id = _stripe_price_id(plan_tier, billing_cycle)
        if not price_id:
            raise ServiceUnavailableError(
                f"No Stripe price configured for {plan_tier}/{billing_cycle}"
            )

        stripe.api_key = settings.stripe_secret_key

        if not org.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email, name=org.name, metadata={"organization_id": str(org.id)}
            )
            org.stripe_customer_id = customer.id
            self.db.commit()

        session = stripe.checkout.Session.create(
            customer=org.stripe_customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{settings.frontend_url}/dashboard?checkout=success",
            cancel_url=f"{settings.landing_url}/?checkout=cancelled",
            metadata={
                "organization_id": str(org.id),
                "plan_tier": plan_tier,
                "billing_cycle": billing_cycle,
            },
        )
        return {"status": "created", "checkout_url": session.url, "contact_sales": False, "message": None}

    def handle_webhook(self, payload: bytes, sig_header: str | None) -> None:
        if not settings.stripe_webhook_secret:
            raise ServiceUnavailableError("Stripe webhook secret is not configured")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
        except (ValueError, stripe.error.SignatureVerificationError) as exc:
            raise ValidationError("signature", f"Invalid Stripe webhook payload: {exc}")

        event_type = event["type"]
        data = event["data"]["object"]

        if event_type == "checkout.session.completed":
            self._handle_checkout_completed(data)
        elif event_type == "customer.subscription.updated":
            self._handle_subscription_updated(data)
        elif event_type == "customer.subscription.deleted":
            self._handle_subscription_deleted(data)
        elif event_type == "invoice.payment_failed":
            self._handle_payment_failed(data)

    def _handle_checkout_completed(self, session: dict) -> None:
        organization_id = (session.get("metadata") or {}).get("organization_id")
        if not organization_id:
            return
        org = self.db.get(Organization, uuid.UUID(organization_id))
        if not org:
            return

        plan_tier = session["metadata"].get("plan_tier", "hobbyist")
        billing_cycle = session["metadata"].get("billing_cycle", "monthly")

        subscription = Subscription(
            organization_id=org.id,
            tier=plan_tier,
            status="active",
            stripe_subscription_id=session.get("subscription"),
            billing_cycle=billing_cycle,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(subscription)
        org.subscription_tier = plan_tier
        self.db.commit()

    def _handle_subscription_updated(self, subscription: dict) -> None:
        row = (
            self.db.query(Subscription)
            .filter(Subscription.stripe_subscription_id == subscription["id"])
            .first()
        )
        if not row:
            return
        row.status = _STRIPE_STATUS_MAP.get(subscription.get("status"), "past_due")
        period_end = subscription.get("current_period_end")
        if period_end:
            row.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)
        self.db.commit()

    def _handle_subscription_deleted(self, subscription: dict) -> None:
        row = (
            self.db.query(Subscription)
            .filter(Subscription.stripe_subscription_id == subscription["id"])
            .first()
        )
        if not row:
            return
        row.status = "cancelled"
        row.ended_at = datetime.now(timezone.utc)
        org = self.db.get(Organization, row.organization_id)
        if org:
            org.subscription_tier = "free"
        self.db.commit()

    def _handle_payment_failed(self, invoice: dict) -> None:
        customer_id = invoice.get("customer")
        org = self.db.query(Organization).filter(Organization.stripe_customer_id == customer_id).first()
        if not org:
            return
        owner = self.db.get(User, org.owner_id)
        if not owner:
            return
        amount = (invoice.get("amount_due") or 0) / 100
        try:
            email_service.send_payment_failed(owner.email, owner.name, amount, org.subscription_tier)
        except Exception:
            # Best-effort notification — the webhook must still 200 to Stripe
            # even if the outbound email fails, or Stripe will keep retrying.
            logger.exception("Failed to send payment-failed email to %s", owner.email)
