import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.teams.schemas import AddTeamMemberRequest, UpdateTeamRequest
from app.models.organization import Organization, Team
from app.models.user import User


class TeamService:
    def __init__(self, db: Session):
        self.db = db

    def _get_with_access(self, team_id: uuid.UUID, user: User) -> Team:
        team = self.db.get(Team, team_id)
        if not team:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Team not found")
        org = self.db.get(Organization, team.organization_id)
        if not org or org.owner_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions on this team")
        return team

    def get(self, team_id: uuid.UUID, user: User) -> Team:
        return self._get_with_access(team_id, user)

    def update(self, team_id: uuid.UUID, payload: UpdateTeamRequest, user: User) -> Team:
        team = self._get_with_access(team_id, user)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(team, field, value)
        self.db.commit()
        self.db.refresh(team)
        return team

    def add_member(self, team_id: uuid.UUID, payload: AddTeamMemberRequest, user: User) -> Team:
        team = self._get_with_access(team_id, user)
        target = self.db.get(User, payload.user_id)
        if not target:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

        members = [m for m in team.members if m.get("user_id") != str(payload.user_id)]
        members.append({"user_id": str(payload.user_id), "role": payload.role})
        team.members = members
        self.db.commit()
        self.db.refresh(team)
        return team

    def remove_member(self, team_id: uuid.UUID, user_id: uuid.UUID, user: User) -> Team:
        team = self._get_with_access(team_id, user)
        team.members = [m for m in team.members if m.get("user_id") != str(user_id)]
        self.db.commit()
        self.db.refresh(team)
        return team
