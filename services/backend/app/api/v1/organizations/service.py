import uuid

from sqlalchemy.orm import Session

from app.api.v1.organizations.schemas import (
    CreateOrganizationRequest,
    CreateTeamRequest,
    UpdateOrganizationRequest,
)
from app.core.exceptions import NotFoundError
from app.models.organization import Organization, Team
from app.models.user import User


class OrganizationService:
    def __init__(self, db: Session):
        self.db = db

    def list_for_user(self, user: User) -> list[Organization]:
        return (
            self.db.query(Organization)
            .filter(Organization.owner_id == user.id)
            .order_by(Organization.created_at.desc())
            .all()
        )

    def get(self, organization_id: uuid.UUID, user: User) -> Organization:
        org = self.db.get(Organization, organization_id)
        if not org or org.owner_id != user.id:
            raise NotFoundError("Organization", organization_id)
        return org

    def create(self, payload: CreateOrganizationRequest, user: User) -> Organization:
        org = Organization(name=payload.name, owner_id=user.id)
        self.db.add(org)
        self.db.commit()
        self.db.refresh(org)
        return org

    def update(
        self, organization_id: uuid.UUID, payload: UpdateOrganizationRequest, user: User
    ) -> Organization:
        org = self.get(organization_id, user)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(org, field, value)
        self.db.commit()
        self.db.refresh(org)
        return org

    def list_teams(self, organization_id: uuid.UUID, user: User) -> list[Team]:
        self.get(organization_id, user)
        return self.db.query(Team).filter(Team.organization_id == organization_id).all()

    def create_team(
        self, organization_id: uuid.UUID, payload: CreateTeamRequest, user: User
    ) -> Team:
        self.get(organization_id, user)
        team = Team(organization_id=organization_id, name=payload.name)
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team
