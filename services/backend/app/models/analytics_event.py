import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import UUIDPKMixin


class AnalyticsEvent(Base, UUIDPKMixin):
    """Marketing/conversion-funnel events (page views, CTA clicks, signup
    steps) — distinct from AuditLog, which tracks compliance-sensitive
    actions on specific resources."""

    __tablename__ = "analytics_events"

    event_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    properties: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
