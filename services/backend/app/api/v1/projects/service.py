import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.projects.schemas import CreateProjectRequest, UpdateProjectRequest
from app.models.project import Project
from app.models.user import User


class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    def list_for_user(self, user: User) -> list[Project]:
        return (
            self.db.query(Project)
            .filter(Project.owner_id == user.id)
            .order_by(Project.created_at.desc())
            .all()
        )

    def get(self, project_id: uuid.UUID, user: User) -> Project:
        project = self.db.get(Project, project_id)
        if not project or project.owner_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
        return project

    def create(self, payload: CreateProjectRequest, user: User) -> Project:
        project = Project(
            organization_id=payload.organization_id,
            team_id=payload.team_id,
            name=payload.name,
            description=payload.description,
            owner_id=user.id,
            type=payload.type,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def update(self, project_id: uuid.UUID, payload: UpdateProjectRequest, user: User) -> Project:
        project = self.get(project_id, user)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project_id: uuid.UUID, user: User) -> None:
        project = self.get(project_id, user)
        self.db.delete(project)
        self.db.commit()
