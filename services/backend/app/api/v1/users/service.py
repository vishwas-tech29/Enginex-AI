from sqlalchemy.orm import Session

from app.api.v1.users.schemas import UpdateProfileRequest
from app.models.user import User


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def update_profile(self, user: User, payload: UpdateProfileRequest) -> User:
        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return user
