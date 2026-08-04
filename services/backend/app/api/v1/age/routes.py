from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.v1.age.schemas import AgeStatusResponse, AgeVerificationRequest, AgeVerificationResponse
from app.api.v1.age.service import AgeVerificationService
from app.api.v1.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/age", tags=["Age Verification"])


@router.post("/verify", response_model=AgeVerificationResponse)
def verify_age(
    payload: AgeVerificationRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AgeVerificationService(db).verify(current_user, payload, request)


@router.get("/status", response_model=AgeStatusResponse)
def get_verification_status(current_user: User = Depends(get_current_user)):
    return {"verified": current_user.age_verified, "verified_at": current_user.age_verified_at}
