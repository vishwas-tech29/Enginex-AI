from datetime import datetime, timezone

from fastapi import Request
from sqlalchemy.orm import Session

from app.api.v1.age.schemas import AgeVerificationRequest
from app.core.exceptions import ValidationError
from app.models.usage_log import AuditLog
from app.models.user import User

MINIMUM_AGE = 18


class AgeVerificationService:
    def __init__(self, db: Session):
        self.db = db

    def verify(self, user: User, payload: AgeVerificationRequest, request: Request) -> dict:
        current_year = datetime.now(timezone.utc).year
        age = current_year - payload.birth_year
        ip_address = request.client.host if request.client else None

        if age < MINIMUM_AGE:
            self._log(user.id, {"age": age, "country": payload.country, "result": "rejected"}, ip_address)
            raise ValidationError("birth_year", f"You must be {MINIMUM_AGE} or older (calculated age: {age})")

        now = datetime.now(timezone.utc)
        user.age_verified = True
        user.birth_year = payload.birth_year
        user.age_verified_at = now
        user.age_verification_country = payload.country
        self.db.commit()

        self._log(user.id, {"age": age, "country": payload.country, "result": "verified"}, ip_address)

        return {"verified": True, "age": age, "verified_at": now}

    def status(self, user: User) -> dict:
        return {"verified": user.age_verified, "verified_at": user.age_verified_at}

    def _log(self, user_id, details: dict, ip_address: str | None) -> None:
        entry = AuditLog(
            user_id=user_id,
            action="age_verification",
            resource_type="user",
            resource_id=user_id,
            details=details,
            ip_address=ip_address,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(entry)
        self.db.commit()
