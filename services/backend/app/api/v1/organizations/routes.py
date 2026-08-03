import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.organizations.schemas import (
    CreateOrganizationRequest,
    CreateTeamRequest,
    OrganizationOut,
    TeamOut,
    UpdateOrganizationRequest,
)
from app.api.v1.organizations.service import OrganizationService
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("", response_model=list[OrganizationOut])
def list_organizations(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return OrganizationService(db).list_for_user(current_user)


@router.post("", response_model=OrganizationOut, status_code=201)
def create_organization(
    payload: CreateOrganizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrganizationService(db).create(payload, current_user)


@router.get("/{org_id}", response_model=OrganizationOut)
def get_organization(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrganizationService(db).get(org_id, current_user)


@router.put("/{org_id}", response_model=OrganizationOut)
def update_organization(
    org_id: uuid.UUID,
    payload: UpdateOrganizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrganizationService(db).update(org_id, payload, current_user)


@router.get("/{org_id}/teams", response_model=list[TeamOut])
def list_teams(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrganizationService(db).list_teams(org_id, current_user)


@router.post("/{org_id}/teams", response_model=TeamOut, status_code=201)
def create_team(
    org_id: uuid.UUID,
    payload: CreateTeamRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrganizationService(db).create_team(org_id, payload, current_user)
