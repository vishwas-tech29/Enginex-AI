import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.v1.auth import oauth
from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.auth.schemas import (
    ConfirmPasswordResetRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RequestPasswordResetRequest,
    TokenResponse,
    UserOut,
)
from app.api.v1.auth.service import AuthService, resolve_plan_tier
from app.config import settings
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    return AuthService(db).register(payload)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    return AuthService(db).login(payload, request)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    return AuthService(db).refresh(payload.refresh_token)


@router.post("/logout", status_code=204)
def logout(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    AuthService(db).logout(current_user, request)
    return None


@router.post("/password-reset", status_code=202)
@limiter.limit("3/minute")
def request_password_reset(request: Request, payload: RequestPasswordResetRequest, db: Session = Depends(get_db)):
    AuthService(db).request_password_reset(payload.email)
    # Always 202, regardless of whether the email exists — don't let this
    # endpoint be usable to enumerate registered accounts.
    return {"status": "If that email is registered, a reset link has been sent."}


@router.post("/password-reset/confirm", status_code=200)
def confirm_password_reset(payload: ConfirmPasswordResetRequest, db: Session = Depends(get_db)):
    AuthService(db).confirm_password_reset(payload.token, payload.new_password)
    return {"status": "Password reset successfully."}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.plan_tier = resolve_plan_tier(db, current_user.id)
    return current_user


# --- OAuth (Google / GitHub) -------------------------------------------------
# Popup flow: frontend opens a popup at .../authorize, which 307s to the
# provider, which redirects back to .../callback, which posts tokens to
# window.opener and closes itself. See app/api/v1/auth/oauth.py.


@router.get("/oauth/{provider}/authorize")
def oauth_authorize(provider: str):
    return RedirectResponse(oauth.build_authorize_url(provider))


@router.get("/oauth/{provider}/callback", response_class=HTMLResponse)
def oauth_callback(provider: str, code: str, state: str, request: Request, db: Session = Depends(get_db)):
    user_info = oauth.exchange_code_for_user_info(provider, code, state)
    user = oauth.find_or_create_user(db, provider, user_info)
    tokens = AuthService(db).complete_login(user, request)

    # JSON-encoded and `<` escaped so nothing in the payload (all sourced
    # from the OAuth provider) can break out of the inline <script> tag.
    message = json.dumps({"type": "oauth_success", **tokens.model_dump(mode="json")}).replace("<", "\\u003c")
    html = f"""<!doctype html>
<html><body>
<script>
  window.opener.postMessage({message}, {json.dumps(settings.frontend_url)});
  window.close();
</script>
</body></html>"""
    return HTMLResponse(html)
