"""Google/GitHub OAuth — the standard popup flow: the frontend opens a
popup pointed at /oauth/{provider}/authorize, which 307s straight to the
provider, which redirects back to /oauth/{provider}/callback, which
exchanges the code, finds-or-creates the user, and returns a tiny HTML page
that posts the tokens back to window.opener and closes itself.

Client ID/Secret are optional settings (see app.config) — sign-in with an
unconfigured provider raises ServiceUnavailableError (503) rather than
sending the browser into a redirect to nowhere, the same pattern
BillingService uses for an unconfigured Stripe key.
"""

import secrets
import time
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import ServiceUnavailableError, ValidationError
from app.models.user import User

STATE_TOKEN_TYPE = "oauth_state"
STATE_TOKEN_MAX_AGE_SECONDS = 300

PROVIDERS: dict[str, dict[str, str]] = {
    "google": {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scope": "openid email profile",
    },
    "github": {
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scope": "read:user user:email",
    },
}


def _provider_config(provider: str) -> dict[str, str]:
    config = PROVIDERS.get(provider)
    if not config:
        raise ValidationError("provider", f"Unknown OAuth provider: {provider}")
    return config


def _client_credentials(provider: str) -> tuple[str, str]:
    client_id = getattr(settings, f"{provider}_client_id", None)
    client_secret = getattr(settings, f"{provider}_client_secret", None)
    if not client_id or not client_secret:
        raise ServiceUnavailableError(f"{provider.title()} sign-in is not configured on this server yet")
    return client_id, client_secret


def _redirect_uri(provider: str) -> str:
    return f"{settings.backend_url}/api/v1/auth/oauth/{provider}/callback"


def _create_state_token() -> str:
    payload = {"type": STATE_TOKEN_TYPE, "nonce": secrets.token_urlsafe(16), "iat": int(time.time())}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _verify_state_token(state: str) -> None:
    try:
        payload = jwt.decode(state, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid OAuth state")
    if payload.get("type") != STATE_TOKEN_TYPE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid OAuth state")
    if time.time() - payload.get("iat", 0) > STATE_TOKEN_MAX_AGE_SECONDS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "OAuth state expired — please try again")


def build_authorize_url(provider: str) -> str:
    config = _provider_config(provider)
    client_id, _ = _client_credentials(provider)
    params = {
        "client_id": client_id,
        "redirect_uri": _redirect_uri(provider),
        "scope": config["scope"],
        "state": _create_state_token(),
        "response_type": "code",
    }
    if provider == "google":
        params["access_type"] = "online"
        params["prompt"] = "select_account"
    return f"{config['authorize_url']}?{urlencode(params)}"


def _fetch_github_primary_email(access_token: str) -> str | None:
    # GitHub's /user only includes `email` if the user made it public.
    # /user/emails (needs the user:email scope) has the real primary one.
    response = httpx.get(
        "https://api.github.com/user/emails",
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        timeout=10,
    )
    response.raise_for_status()
    primary = next((e for e in response.json() if e.get("primary")), None)
    return primary["email"] if primary else None


def exchange_code_for_user_info(provider: str, code: str, state: str) -> dict:
    _verify_state_token(state)
    config = _provider_config(provider)
    client_id, client_secret = _client_credentials(provider)

    token_response = httpx.post(
        config["token_url"],
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": _redirect_uri(provider),
            "grant_type": "authorization_code",
        },
        headers={"Accept": "application/json"},
        timeout=10,
    )
    token_response.raise_for_status()
    access_token = token_response.json().get("access_token")
    if not access_token:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"{provider.title()} did not return an access token")

    userinfo_response = httpx.get(
        config["userinfo_url"],
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        timeout=10,
    )
    userinfo_response.raise_for_status()
    data = userinfo_response.json()

    if provider == "github":
        email = data.get("email") or _fetch_github_primary_email(access_token)
        return {
            "id": str(data["id"]),
            "email": email,
            "name": data.get("name") or data.get("login"),
            "avatar": data.get("avatar_url"),
        }

    return {"id": data["sub"], "email": data.get("email"), "name": data.get("name"), "avatar": data.get("picture")}


def find_or_create_user(db: Session, provider: str, user_info: dict) -> User:
    if not user_info.get("email"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{provider.title()} account has no accessible email")

    user = db.query(User).filter(User.oauth_provider == provider, User.oauth_id == user_info["id"]).first()
    if user:
        return user

    user = db.query(User).filter(User.email == user_info["email"]).first()
    if user:
        # An existing password account signing in with OAuth for the first
        # time — link it rather than creating a duplicate.
        user.oauth_provider = provider
        user.oauth_id = user_info["id"]
        db.commit()
        return user

    user = User(
        email=user_info["email"],
        name=user_info.get("name") or user_info["email"].split("@")[0],
        avatar=user_info.get("avatar"),
        oauth_provider=provider,
        oauth_id=user_info["id"],
        password_hash=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
