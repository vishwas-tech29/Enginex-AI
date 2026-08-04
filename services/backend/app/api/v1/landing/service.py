import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.api.v1.auth.schemas import RegisterRequest
from app.api.v1.auth.service import AuthService
from app.api.v1.billing.service import PAID_TIERS, PLAN_FEATURES, BillingService
from app.api.v1.landing.analytics_service import AnalyticsService
from app.api.v1.landing.schemas import SignupRequest
from app.core.exceptions import ConflictError, ServiceUnavailableError
from app.email.service import email_service
from app.models.organization import Organization
from app.models.user import User

logger = logging.getLogger("enginex.landing")

TRIAL_DAYS = 14


def _feature_summary(features: dict) -> list[str]:
    lines = []
    if features["projects_limit"] is None:
        lines.append("Unlimited projects")
    else:
        lines.append(f"Up to {features['projects_limit']} project(s)")
    storage = features["storage_gb"]
    lines.append("Unlimited storage" if storage is None else f"{storage}GB storage")
    if features["ai_suggestions"]:
        lines.append("AI design suggestions")
    collab = features["collaboration_users"]
    if collab and collab > 1:
        lines.append(f"Real-time collaboration for up to {collab} users")
    elif collab is None:
        lines.append("Unlimited collaborators")
    if features["simulation"]:
        lines.append("Simulation")
    return lines


class LandingService:
    def __init__(self, db: Session):
        self.db = db

    def signup(self, payload: SignupRequest) -> dict:
        existing = self.db.query(User).filter(User.email == payload.email).first()
        if existing:
            # NOTE: deliberately NOT returning the existing user's tokens for
            # a re-submitted email (an illustrative version of this endpoint
            # did that) — doing so without a password check would be an
            # account-takeover bug: anyone could "sign up" with a stranger's
            # email and receive a live session for their account.
            raise ConflictError("An account with this email already exists — please log in instead")

        tokens = AuthService(self.db).register(
            RegisterRequest(email=payload.email, password=payload.password, name=payload.name)
        )

        is_paid = payload.plan_tier in PAID_TIERS
        trial_ends = datetime.now(timezone.utc) + timedelta(days=TRIAL_DAYS) if is_paid else None

        user = self.db.query(User).filter(User.email == payload.email).first()
        user.created_from = "landing_page"
        user.referral_source = payload.referral_source
        user.company = payload.company
        user.trial_ends = trial_ends
        self.db.commit()
        self.db.refresh(user)

        org = Organization(name=f"{payload.name}'s Organization", owner_id=user.id)
        self.db.add(org)
        self.db.commit()
        self.db.refresh(org)

        checkout_url = None
        contact_sales = payload.plan_tier == "enterprise"
        if is_paid:
            try:
                result = BillingService(self.db).create_checkout_session(
                    org.id, payload.plan_tier, "monthly", user
                )
                checkout_url = result.get("checkout_url")
            except ServiceUnavailableError:
                # Billing isn't configured in this environment — the account
                # is still created; checkout just isn't offered yet.
                logger.info("Stripe not configured — signup completed without a checkout session")

        features = PLAN_FEATURES.get(payload.plan_tier, PLAN_FEATURES["free"])
        try:
            email_service.send_welcome(
                user.email,
                user.name,
                payload.plan_tier,
                _feature_summary(features),
                trial_ends.isoformat() if trial_ends else None,
            )
        except Exception:
            logger.exception("Failed to send welcome email to %s", user.email)

        AnalyticsService(self.db).track(
            event_name="signup_completed",
            user_id=user.id,
            properties={
                "plan": payload.plan_tier,
                "source": payload.referral_source,
                "company": payload.company,
            },
        )

        return {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_type": tokens.token_type,
            "user": tokens.user,
            "organization_id": org.id,
            "checkout_url": checkout_url,
            "contact_sales": contact_sales,
            "trial_ends": trial_ends,
        }
