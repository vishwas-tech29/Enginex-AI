import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.projects.schemas import CreateProjectRequest, ProjectOut, UpdateProjectRequest
from app.api.v1.projects.service import ProjectService
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ProjectService(db).list_for_user(current_user)


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    payload: CreateProjectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProjectService(db).create(payload, current_user)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProjectService(db).get(project_id, current_user)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: uuid.UUID,
    payload: UpdateProjectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProjectService(db).update(project_id, payload, current_user)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ProjectService(db).delete(project_id, current_user)
    return None
