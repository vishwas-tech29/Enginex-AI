import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.folders.schemas import CreateFolderRequest, MoveFolderRequest, UpdateFolderRequest
from app.api.v1.projects.service import ROLE_EDITOR, ROLE_VIEWER, ProjectService
from app.core.exceptions import NotFoundError
from app.models.project import Folder, Project


class FolderService:
    def __init__(self, db: Session):
        self.db = db
        self.projects = ProjectService(db)

    def _project_for(self, project_id: uuid.UUID, user, min_role: str) -> Project:
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        self.projects.require_access(project, user, min_role)
        return project

    def list_for_project(self, project_id: uuid.UUID, user) -> list[Folder]:
        self._project_for(project_id, user, ROLE_VIEWER)
        return self.db.query(Folder).filter(Folder.project_id == project_id).all()

    def get(self, folder_id: uuid.UUID, user, min_role: str = ROLE_VIEWER) -> Folder:
        folder = self.db.get(Folder, folder_id)
        if not folder:
            raise NotFoundError("Folder", folder_id)
        self._project_for(folder.project_id, user, min_role)
        return folder

    def create(self, project_id: uuid.UUID, payload: CreateFolderRequest, user) -> Folder:
        self._project_for(project_id, user, ROLE_EDITOR)
        folder = Folder(
            project_id=project_id,
            parent_id=payload.parent_id,
            name=payload.name,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(folder)
        self.db.commit()
        self.db.refresh(folder)
        return folder

    def update(self, folder_id: uuid.UUID, payload: UpdateFolderRequest, user) -> Folder:
        folder = self.get(folder_id, user, ROLE_EDITOR)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(folder, field, value)
        self.db.commit()
        self.db.refresh(folder)
        return folder

    def move(self, folder_id: uuid.UUID, payload: MoveFolderRequest, user) -> Folder:
        folder = self.get(folder_id, user, ROLE_EDITOR)
        if payload.parent_id == folder_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "A folder cannot be its own parent")
        folder.parent_id = payload.parent_id
        self.db.commit()
        self.db.refresh(folder)
        return folder

    def delete(self, folder_id: uuid.UUID, user) -> None:
        folder = self.get(folder_id, user, ROLE_EDITOR)
        self.db.delete(folder)
        self.db.commit()
