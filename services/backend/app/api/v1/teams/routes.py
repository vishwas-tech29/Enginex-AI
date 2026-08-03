import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.teams.schemas import AddTeamMemberRequest, TeamOut, UpdateTeamRequest
from app.api.v1.teams.service import TeamService
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("/{team_id}", response_model=TeamOut)
def get_team(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TeamService(db).get(team_id, current_user)


@router.put("/{team_id}", response_model=TeamOut)
def update_team(
    team_id: uuid.UUID,
    payload: UpdateTeamRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TeamService(db).update(team_id, payload, current_user)


@router.post("/{team_id}/members", response_model=TeamOut, status_code=201)
def add_member(
    team_id: uuid.UUID,
    payload: AddTeamMemberRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TeamService(db).add_member(team_id, payload, current_user)


@router.delete("/{team_id}/members/{user_id}", response_model=TeamOut)
def remove_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TeamService(db).remove_member(team_id, user_id, current_user)
