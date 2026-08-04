"""Landing page signup, Stripe billing, age verification, and analytics —
all real: real user/org creation through the existing auth stack, real
DB-persisted analytics events and audit log entries, and a real (mocked at
the stripe SDK boundary, not at our service boundary) Stripe checkout flow."""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.config import settings
from app.models.analytics_event import AnalyticsEvent
from app.models.organization import Organization
from app.models.subscription import Subscription
from app.models.usage_log import AuditLog
from app.models.user import User


def test_landing_pricing_lists_all_tiers(client):
    response = client.get("/api/v1/landing/pricing")
    assert response.status_code == 200
    tiers = {plan["tier"] for plan in response.json()["plans"]}
    assert tiers == {"free", "hobbyist", "professional", "enterprise"}
    professional = next(p for p in response.json()["plans"] if p["tier"] == "professional")
    assert professional["price_monthly"] == 99
    assert professional["features"]["simulation"] is True
    enterprise = next(p for p in response.json()["plans"] if p["tier"] == "enterprise")
    assert enterprise["is_custom"] is True


def test_signup_creates_a_real_usable_account(client, db_session):
    response = client.post(
        "/api/v1/landing/signup",
        json={
            "email": "signup1@example.com",
            "password": "Sup3rSecret1",
            "name": "Ada Lovelace",
            "plan_tier": "free",
            "company": "Acme Robotics",
            "referral_source": "google",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["trial_ends"] is None  # free tier gets no trial
    assert body["contact_sales"] is False
    assert body["checkout_url"] is None

    # The returned access token is real and immediately usable.
    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["email"] == "signup1@example.com"

    user = db_session.query(User).filter(User.email == "signup1@example.com").first()
    assert user.created_from == "landing_page"
    assert user.company == "Acme Robotics"
    assert user.referral_source == "google"

    org = db_session.get(Organization, uuid.UUID(body["organization_id"]))
    assert org.owner_id == user.id
    assert org.name == "Ada Lovelace's Organization"


def test_signup_duplicate_email_conflicts_without_leaking_tokens(client):
    payload = {
        "email": "dupe@example.com",
        "password": "Sup3rSecret1",
        "name": "First User",
        "plan_tier": "free",
    }
    first = client.post("/api/v1/landing/signup", json=payload)
    assert first.status_code == 201

    second = client.post(
        "/api/v1/landing/signup",
        json={**payload, "name": "Attacker Pretending"},
    )
    assert second.status_code == 409
    assert "access_token" not in second.json()


def test_signup_paid_tier_sets_trial_and_skips_checkout_when_stripe_unconfigured(client, db_session):
    assert settings.stripe_secret_key is None  # sanity: this env has no real key
    response = client.post(
        "/api/v1/landing/signup",
        json={
            "email": "paiduser@example.com",
            "password": "Sup3rSecret1",
            "name": "Grace Hopper",
            "plan_tier": "hobbyist",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["trial_ends"] is not None
    assert body["checkout_url"] is None  # no hard failure — just no checkout offered

    user = db_session.query(User).filter(User.email == "paiduser@example.com").first()
    assert user.trial_ends is not None


def test_analytics_event_persists_to_db(client, db_session):
    response = client.post(
        "/api/v1/landing/analytics/event",
        json={"event": "cta_clicked", "properties": {"tier": "professional"}, "url": "https://velorah.io/"},
        headers={"User-Agent": "pytest-agent"},
    )
    assert response.status_code == 202

    event = db_session.query(AnalyticsEvent).filter(AnalyticsEvent.event_name == "cta_clicked").first()
    assert event is not None
    assert event.properties == {"tier": "professional"}
    assert event.url == "https://velorah.io/"
    assert event.user_agent == "pytest-agent"
    assert event.user_id is None  # anonymous, no bearer token sent


def _signup(client, email="ageuser@example.com"):
    response = client.post(
        "/api/v1/landing/signup",
        json={"email": email, "password": "Sup3rSecret1", "name": "Alan Turing", "plan_tier": "free"},
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_age_verification_rejects_under_18(client, db_session):
    headers = _signup(client, "under18@example.com")
    this_year = datetime.now(timezone.utc).year
    response = client.post(
        "/api/v1/age/verify",
        json={"birth_year": this_year - 10, "country": "US"},
        headers=headers,
    )
    assert response.status_code == 422

    status = client.get("/api/v1/age/status", headers=headers)
    assert status.json()["verified"] is False

    audit_entries = db_session.query(AuditLog).filter(AuditLog.action == "age_verification").all()
    assert any(entry.details.get("result") == "rejected" for entry in audit_entries)


def test_age_verification_accepts_18_plus_and_logs_audit_entry(client, db_session):
    headers = _signup(client, "over18@example.com")
    this_year = datetime.now(timezone.utc).year
    response = client.post(
        "/api/v1/age/verify",
        json={"birth_year": this_year - 25, "country": "US"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["verified"] is True
    assert body["age"] == 25

    status = client.get("/api/v1/age/status", headers=headers)
    assert status.json()["verified"] is True
    assert status.json()["verified_at"] is not None

    user = db_session.query(User).filter(User.email == "over18@example.com").first()
    assert user.age_verified is True
    assert user.birth_year == this_year - 25

    audit_entries = db_session.query(AuditLog).filter(AuditLog.action == "age_verification").all()
    assert len(audit_entries) >= 1


def test_billing_checkout_returns_503_when_stripe_not_configured(client):
    assert settings.stripe_secret_key is None
    signup = client.post(
        "/api/v1/landing/signup",
        json={"email": "billing1@example.com", "password": "Sup3rSecret1", "name": "Org Owner", "plan_tier": "free"},
    )
    headers = {"Authorization": f"Bearer {signup.json()['access_token']}"}
    org_id = signup.json()["organization_id"]

    response = client.post(
        "/api/v1/billing/checkout",
        json={"organization_id": org_id, "plan_tier": "hobbyist", "billing_cycle": "monthly"},
        headers=headers,
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_billing_checkout_creates_real_stripe_session_when_configured(client, db_session, monkeypatch):
    signup = client.post(
        "/api/v1/landing/signup",
        json={"email": "billing2@example.com", "password": "Sup3rSecret1", "name": "Org Owner Two", "plan_tier": "free"},
    )
    headers = {"Authorization": f"Bearer {signup.json()['access_token']}"}
    org_id = signup.json()["organization_id"]

    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_fake")
    monkeypatch.setattr(settings, "stripe_price_hobbyist_monthly", "price_test_hobbyist_monthly")

    fake_customer = MagicMock(id="cus_fake123")
    fake_session = MagicMock(url="https://checkout.stripe.com/pay/cs_test_fake")

    import stripe

    monkeypatch.setattr(stripe.Customer, "create", MagicMock(return_value=fake_customer))
    monkeypatch.setattr(stripe.checkout.Session, "create", MagicMock(return_value=fake_session))

    response = client.post(
        "/api/v1/billing/checkout",
        json={"organization_id": org_id, "plan_tier": "hobbyist", "billing_cycle": "monthly"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["checkout_url"] == "https://checkout.stripe.com/pay/cs_test_fake"

    stripe.checkout.Session.create.assert_called_once()
    call_kwargs = stripe.checkout.Session.create.call_args.kwargs
    assert call_kwargs["line_items"][0]["price"] == "price_test_hobbyist_monthly"
    assert call_kwargs["customer"] == "cus_fake123"

    org = db_session.get(Organization, uuid.UUID(org_id))
    assert org.stripe_customer_id == "cus_fake123"


def test_stripe_webhook_checkout_completed_creates_subscription(client, db_session, monkeypatch):
    signup = client.post(
        "/api/v1/landing/signup",
        json={"email": "webhookorg@example.com", "password": "Sup3rSecret1", "name": "Webhook Org", "plan_tier": "free"},
    )
    org_id = signup.json()["organization_id"]

    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_fake")

    fake_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "subscription": "sub_fake123",
                "metadata": {"organization_id": org_id, "plan_tier": "professional", "billing_cycle": "annual"},
            }
        },
    }

    import stripe

    monkeypatch.setattr(stripe.Webhook, "construct_event", MagicMock(return_value=fake_event))

    response = client.post(
        "/api/v1/billing/webhook",
        content=b"{}",
        headers={"stripe-signature": "t=1,v1=fake"},
    )
    assert response.status_code == 200, response.text

    subscription = (
        db_session.query(Subscription).filter(Subscription.stripe_subscription_id == "sub_fake123").first()
    )
    assert subscription is not None
    assert subscription.tier == "professional"
    assert subscription.billing_cycle == "annual"

    org = db_session.get(Organization, uuid.UUID(org_id))
    assert org.subscription_tier == "professional"
