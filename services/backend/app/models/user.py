from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class User(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar: Mapped[str | None] = mapped_column(Text, nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Landing-page / growth attribution — set on signup, never overwritten after.
    created_from: Mapped[str | None] = mapped_column(String(50), nullable=True)
    referral_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    trial_ends: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Age verification. birth_year is intentionally the only PII stored (not
    # a full DOB) to keep the compliance surface small; it is NOT encrypted
    # at rest — real field-level encryption (pgcrypto / KMS-backed) is a
    # follow-up, not implemented here.
    age_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    age_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    age_verification_country: Mapped[str | None] = mapped_column(String(2), nullable=True)
