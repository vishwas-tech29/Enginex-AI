import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.usage_log import UsageLog
from app.models.user import User

logger = logging.getLogger("enginex.ai.usage")


def _resolve_organization_id(db: Session, user: User, project_id: uuid.UUID | None) -> uuid.UUID | None:
    if project_id:
        project = db.get(Project, project_id)
        if project:
            return project.organization_id

    from app.models.organization import Organization

    org = db.query(Organization).filter(Organization.owner_id == user.id).first()
    return org.id if org else None


class UsageAnalytics:
    """Persist and summarize AI token/cost usage, backed by the existing
    `usage_logs` table (see app/models/usage_log.py)."""

    def __init__(self, db: Session):
        self.db = db

    def log_llm_call(
        self,
        user: User,
        operation: str,
        provider: str,
        model: str,
        tokens_input: int,
        tokens_output: int,
        cost: float,
        project_id: uuid.UUID | None = None,
        resource_id: uuid.UUID | None = None,
    ) -> UsageLog | None:
        organization_id = _resolve_organization_id(self.db, user, project_id)
        if organization_id is None:
            logger.warning("usage_log_skipped_no_org", extra={"user_id": str(user.id)})
            return None

        log = UsageLog(
            organization_id=organization_id,
            user_id=user.id,
            operation=f"{operation}:{provider}:{model}",
            resource_id=resource_id,
            tokens_used=tokens_input + tokens_output,
            cost_usd=cost,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(log)
        self.db.commit()
        return log

    def get_user_usage(self, user: User, start_date: datetime, end_date: datetime) -> dict:
        logs = (
            self.db.query(UsageLog)
            .filter(
                UsageLog.user_id == user.id,
                UsageLog.created_at >= start_date,
                UsageLog.created_at <= end_date,
            )
            .all()
        )

        total_tokens = sum(log.tokens_used for log in logs)
        total_cost = sum(float(log.cost_usd) for log in logs)
        calls_by_operation: dict[str, int] = {}
        for log in logs:
            calls_by_operation[log.operation] = calls_by_operation.get(log.operation, 0) + 1

        return {
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "calls_by_operation": calls_by_operation,
            "api_calls": len(logs),
            "average_cost_per_call": round(total_cost / len(logs), 6) if logs else 0.0,
        }

    def get_today_cost(self, user: User) -> float:
        start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        usage = self.get_user_usage(user, start_of_day, datetime.now(timezone.utc))
        return usage["total_cost_usd"]
