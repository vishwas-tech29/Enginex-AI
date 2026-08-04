"""Extended auth coverage added alongside the auth session-management work:
rate limiting, login/logout audit trail + last-login tracking, password
reset, plan_tier on the user payload, and OAuth (mocked at the httpx
boundary, matching how Stripe is mocked at the stripe SDK boundary in
test_landing_billing.py)."""

import time
from unittest.mock import MagicMock

from app.config import settings
from app.models.organization import Organization
from app.models.usage_log import AuditLog
from app.models.user import User
from tests.helpers import register_user


def test_login_records_audit_entry_and_last_login(client, db_session):
    register_user(client, email="loginaudit@enginex.ai")
    response = client.post(
        "/api/v1/auth/login", json={"email": "loginaudit@enginex.ai", "password": "Sup3rSecret1"}
    )
    assert response.status_code == 200

    user = db_session.query(User).filter(User.email == "loginaudit@enginex.ai").first()
    assert user.last_login_at is not None

    entries = db_session.query(AuditLog).filter(AuditLog.user_id == user.id, AuditLog.action == "login").all()
    assert len(entries) == 1


def test_logout_records_audit_entry(client, db_session):
    _, headers = register_user(client, email="logoutaudit@enginex.ai")
    user = db_session.query(User).filter(User.email == "logoutaudit@enginex.ai").first()

    response = client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 204

    entries = db_session.query(AuditLog).filter(AuditLog.user_id == user.id, AuditLog.action == "logout").all()
    assert len(entries) == 1


def test_login_rate_limited_after_five_attempts_per_minute(client):
    register_user(client, email="ratelimited@enginex.ai")

    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login", json={"email": "ratelimited@enginex.ai", "password": "wrong-password"}
        )
        assert response.status_code == 401

    sixth = client.post(
        "/api/v1/auth/login", json={"email": "ratelimited@enginex.ai", "password": "wrong-password"}
    )
    assert sixth.status_code == 429


def test_me_returns_free_plan_tier_by_default(client):
    _, headers = register_user(client, email="freeplan@enginex.ai")
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["plan_tier"] == "free"


def test_me_returns_owned_organizations_plan_tier(client, db_session):
    _, headers = register_user(client, email="paidplan@enginex.ai")
    user = db_session.query(User).filter(User.email == "paidplan@enginex.ai").first()

    org = Organization(name="Paid Org", owner_id=user.id, subscription_tier="professional")
    db_session.add(org)
    db_session.commit()

    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["plan_tier"] == "professional"


def test_password_reset_full_round_trip(client, db_session, monkeypatch):
    register_user(client, email="resetme@enginex.ai", password="OldPassw0rd")

    sent = {}
    monkeypatch.setattr(
        "app.api.v1.auth.service.email_service.send_password_reset",
        lambda to, name, url: sent.update(to=to, url=url) or True,
    )

    request_response = client.post("/api/v1/auth/password-reset", json={"email": "resetme@enginex.ai"})
    assert request_response.status_code == 202
    assert sent["to"] == "resetme@enginex.ai"

    token = sent["url"].split("token=")[1]

    confirm_response = client.post(
        "/api/v1/auth/password-reset/confirm", json={"token": token, "new_password": "NewPassw0rd1"}
    )
    assert confirm_response.status_code == 200

    old_login = client.post(
        "/api/v1/auth/login", json={"email": "resetme@enginex.ai", "password": "OldPassw0rd"}
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login", json={"email": "resetme@enginex.ai", "password": "NewPassw0rd1"}
    )
    assert new_login.status_code == 200


def test_password_reset_for_unknown_email_still_returns_202(client):
    response = client.post("/api/v1/auth/password-reset", json={"email": "nobody@enginex.ai"})
    assert response.status_code == 202


def test_password_reset_confirm_rejects_invalid_token(client):
    response = client.post(
        "/api/v1/auth/password-reset/confirm", json={"token": "not-a-real-token", "new_password": "NewPassw0rd1"}
    )
    assert response.status_code == 401


def test_oauth_authorize_returns_503_when_provider_not_configured(client):
    response = client.get("/api/v1/auth/oauth/google/authorize", follow_redirects=False)
    assert response.status_code == 503


def test_oauth_authorize_unknown_provider_is_a_validation_error(client, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "test-client-id")
    monkeypatch.setattr(settings, "google_client_secret", "test-client-secret")
    response = client.get("/api/v1/auth/oauth/not-a-real-provider/authorize", follow_redirects=False)
    assert response.status_code == 422


def test_oauth_authorize_redirects_to_provider_when_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "test-client-id")
    monkeypatch.setattr(settings, "google_client_secret", "test-client-secret")

    response = client.get("/api/v1/auth/oauth/google/authorize", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"].startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "client_id=test-client-id" in response.headers["location"]


def test_oauth_callback_creates_and_logs_in_a_new_user(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "test-client-id")
    monkeypatch.setattr(settings, "google_client_secret", "test-client-secret")

    authorize = client.get("/api/v1/auth/oauth/google/authorize", follow_redirects=False)
    state = authorize.headers["location"].split("state=")[1].split("&")[0]

    token_response = MagicMock()
    token_response.json.return_value = {"access_token": "fake-google-access-token"}
    token_response.raise_for_status = MagicMock()

    userinfo_response = MagicMock()
    userinfo_response.json.return_value = {
        "sub": "google-user-123",
        "email": "oauthuser@example.com",
        "name": "OAuth User",
        "picture": "https://example.com/avatar.png",
    }
    userinfo_response.raise_for_status = MagicMock()

    monkeypatch.setattr("app.api.v1.auth.oauth.httpx.post", MagicMock(return_value=token_response))
    monkeypatch.setattr("app.api.v1.auth.oauth.httpx.get", MagicMock(return_value=userinfo_response))

    response = client.get(
        f"/api/v1/auth/oauth/google/callback?code=fake-code&state={state}", follow_redirects=False
    )
    assert response.status_code == 200
    assert "oauth_success" in response.text
    assert "oauthuser@example.com" in response.text

    user = db_session.query(User).filter(User.email == "oauthuser@example.com").first()
    assert user is not None
    assert user.oauth_provider == "google"
    assert user.oauth_id == "google-user-123"
    assert user.password_hash is None


def test_oauth_callback_rejects_expired_state(client, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "test-client-id")
    monkeypatch.setattr(settings, "google_client_secret", "test-client-secret")
    monkeypatch.setattr("app.api.v1.auth.oauth.STATE_TOKEN_MAX_AGE_SECONDS", 0)

    authorize = client.get("/api/v1/auth/oauth/google/authorize", follow_redirects=False)
    state = authorize.headers["location"].split("state=")[1].split("&")[0]
    time.sleep(1.1)

    response = client.get(f"/api/v1/auth/oauth/google/callback?code=fake-code&state={state}")
    assert response.status_code == 400
