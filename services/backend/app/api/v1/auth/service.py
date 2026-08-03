import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.models.user import User
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


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

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.db.query(User).filter(User.email == payload.email).first()
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
        return self._issue_tokens(user)

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

    def _issue_tokens(self, user: User) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
            user=UserOut.model_validate(user),
        )
