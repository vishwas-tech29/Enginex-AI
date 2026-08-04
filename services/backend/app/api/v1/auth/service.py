import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.v1.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.config import settings
from app.email.service import email_service
from app.models.organization import Organization
from app.models.usage_log import AuditLog
from app.models.user import User
from app.utils.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def resolve_plan_tier(db: Session, user_id: uuid.UUID) -> str:
    """A user's plan is really their organization's subscription — this app
    doesn't have a separate per-user "current org" selector, so this uses
    the organization they own. Users who don't own one yet (e.g. fresh
    signups before creating/joining an org) are "free"."""
    org = db.query(Organization).filter(Organization.owner_id == user_id).first()
    return org.subscription_tier if org else "free"


def _request_ip(request: Request | None) -> str | None:
    return request.client.host if request and request.client else None


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, payload: RegisterRequest) -> TokenResponse:
        existing = self.db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            name=payload.name,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return self._issue_tokens(user)

    def login(self, payload: LoginRequest, request: Request | None = None) -> TokenResponse:
        user = self.db.query(User).filter(User.email == payload.email).first()
        if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
        return self.complete_login(user, request)

    def complete_login(self, user: User, request: Request | None = None) -> TokenResponse:
        """Record a successful login (any method — password or OAuth) and
        issue tokens. Public so the OAuth callback route can reuse the same
        last-login tracking and audit trail as password login."""
        ip_address = _request_ip(request)
        user.last_login_at = datetime.now(timezone.utc)
        user.last_login_ip = ip_address
        self.db.commit()
        self._audit(user.id, "login", ip_address)
        return self._issue_tokens(user)

    def logout(self, user: User, request: Request | None = None) -> None:
        # Stateless JWTs: client discards tokens. Token revocation/blacklisting
        # can be added via Redis if refresh tokens need server-side invalidation.
        self._audit(user.id, "logout", _request_ip(request))

    def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

        if payload.get("type") != "refresh":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")

        try:
            user_id = uuid.UUID(payload["sub"])
        except (KeyError, ValueError):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token subject")

        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
        return self._issue_tokens(user)

    def request_password_reset(self, email: str) -> None:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            # Deliberately a no-op — the route always returns 202 regardless,
            # so a caller can't use this to test which emails are registered.
            return

        token = create_password_reset_token(user.id)
        reset_url = f"{settings.frontend_url}/reset-password?token={token}"
        email_service.send_password_reset(user.email, user.name, reset_url)
        # AuditLog.action is String(20) — Postgres enforces that even
        # though SQLite (used in tests) silently doesn't, so this has to
        # stay short even though nothing in-repo would catch a regression.
        self._audit(user.id, "reset_requested", None)

    def confirm_password_reset(self, token: str, new_password: str) -> None:
        try:
            payload = decode_token(token)
        except Exception:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired reset link")

        if payload.get("type") != "password_reset":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")

        try:
            user_id = uuid.UUID(payload["sub"])
        except (KeyError, ValueError):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token subject")

        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

        user.password_hash = hash_password(new_password)
        self.db.commit()
        self._audit(user.id, "password_reset", None)
        email_service.send_password_changed(user.email, user.name)

    def _audit(self, user_id: uuid.UUID, action: str, ip_address: str | None) -> None:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type="user",
            resource_id=user_id,
            details={},
            ip_address=ip_address,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(entry)
        self.db.commit()

    def _issue_tokens(self, user: User) -> TokenResponse:
        # `plan_tier` isn't a mapped column — it's an on-demand read of the
        # organization this user owns (see resolve_plan_tier), stashed as a
        # transient attribute so UserOut.model_validate(..., from_attributes)
        # picks it up like any other field.
        user.plan_tier = resolve_plan_tier(self.db, user.id)
        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
            user=UserOut.model_validate(user),
        )
