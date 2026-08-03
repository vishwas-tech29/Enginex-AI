from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.api.v1.auth.service import AuthService
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    return AuthService(db).register(payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return AuthService(db).login(payload)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    return AuthService(db).refresh(payload.refresh_token)


@router.post("/logout", status_code=204)
def logout(current_user: User = Depends(get_current_user)):
    # Stateless JWTs: client discards tokens. Token revocation/blacklisting
    # can be added via Redis if refresh tokens need server-side invalidation.
    return None


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
