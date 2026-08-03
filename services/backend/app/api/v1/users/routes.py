from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.users.schemas import UpdateProfileRequest, UserOut
from app.api.v1.users.service import UserService
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserService(db).update_profile(current_user, payload)
