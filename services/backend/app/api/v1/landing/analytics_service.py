import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.analytics_event import AnalyticsEvent


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def track(
        self,
        event_name: str,
        user_id: uuid.UUID | None = None,
        properties: dict | None = None,
        url: str | None = None,
        user_agent: str | None = None,
    ) -> AnalyticsEvent:
        event = AnalyticsEvent(
            event_name=event_name,
            user_id=user_id,
            properties=properties or {},
            url=url,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
