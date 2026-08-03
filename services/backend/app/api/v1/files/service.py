import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1.projects.service import ROLE_EDITOR, ROLE_VIEWER, ProjectService
from app.config import settings
from app.core.exceptions import NotFoundError
from app.models.file import File
from app.models.file_version import FileVersion
from app.models.project import Project
from app.models.user import User
from app.services.storage import DownloadTarget, get_storage


class FileService:
    def __init__(self, db: Session):
        self.db = db
        self.storage = get_storage()
        self.projects = ProjectService(db)

    def _project_for(self, project_id: uuid.UUID, user: User, min_role: str) -> Project:
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        self.projects.require_access(project, user, min_role)
        return project

    def list_for_project(self, project_id: uuid.UUID, user: User) -> list[File]:
        self._project_for(project_id, user, ROLE_VIEWER)
        return (
            self.db.query(File)
            .filter(File.project_id == project_id, File.is_deleted.is_(False))
            .order_by(File.created_at.desc())
            .all()
        )

    def get(self, file_id: uuid.UUID, user: User, min_role: str = ROLE_VIEWER) -> File:
        file = self.db.get(File, file_id)
        if not file or file.is_deleted:
            raise NotFoundError("File", file_id)
        self._project_for(file.project_id, user, min_role)
        return file

    def upload(
        self,
        project_id: uuid.UUID,
        folder_id: uuid.UUID | None,
        filename: str,
        fileobj: BinaryIO,
        user: User,
    ) -> File:
        self._project_for(project_id, user, ROLE_EDITOR)

        existing = (
            self.db.query(File)
            .filter(
                File.project_id == project_id,
                File.folder_id == folder_id,
                File.name == filename,
                File.is_deleted.is_(False),
            )
            .first()
        )

        now = datetime.now(timezone.utc)
        file_type = Path(filename).suffix.lstrip(".") or "bin"

        if existing:
            version_number = existing.version_number + 1
            file = existing
        else:
            file = File(
                project_id=project_id,
                folder_id=folder_id,
                name=filename,
                type=file_type,
                file_key="",
                created_by=user.id,
            )
            self.db.add(file)
            self.db.flush()
            version_number = 1

        file_key = f"projects/{project_id}/{file.id}/v{version_number}/{filename}"
        size_bytes = self.storage.save(file_key, fileobj)
        if size_bytes > settings.max_upload_size_bytes:
            self.storage.delete(file_key)
            raise HTTPException(413, "File too large")

        file.file_key = file_key
        file.size_bytes = size_bytes
        file.version_number = version_number
        file.type = file_type

        version = FileVersion(
            file_id=file.id,
            version_number=version_number,
            file_key=file_key,
            size_bytes=size_bytes,
            created_by=user.id,
            created_at=now,
        )
        self.db.add(version)
        self.db.commit()
        self.db.refresh(file)
        return file

    def list_versions(self, file_id: uuid.UUID, user: User) -> list[FileVersion]:
        self.get(file_id, user, ROLE_VIEWER)
        return (
            self.db.query(FileVersion)
            .filter(FileVersion.file_id == file_id)
            .order_by(FileVersion.version_number.desc())
            .all()
        )

    def get_download_target(
        self, file_id: uuid.UUID, user: User, version_id: uuid.UUID | None = None
    ) -> tuple[DownloadTarget, str]:
        file = self.get(file_id, user, ROLE_VIEWER)
        if version_id:
            version = self.db.get(FileVersion, version_id)
            if not version or version.file_id != file_id:
                raise NotFoundError("File version", version_id)
            key = version.file_key
        else:
            key = file.file_key
        return self.storage.get_download_target(key), file.name

    def revert_to_version(self, file_id: uuid.UUID, version_id: uuid.UUID, user: User) -> File:
        file = self.get(file_id, user, ROLE_EDITOR)
        version = self.db.get(FileVersion, version_id)
        if not version or version.file_id != file_id:
            raise NotFoundError("File version", version_id)

        new_version_number = file.version_number + 1
        new_version = FileVersion(
            file_id=file.id,
            version_number=new_version_number,
            file_key=version.file_key,
            size_bytes=version.size_bytes,
            created_by=user.id,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(new_version)

        file.file_key = version.file_key
        file.size_bytes = version.size_bytes
        file.version_number = new_version_number
        self.db.commit()
        self.db.refresh(file)
        return file

    def delete(self, file_id: uuid.UUID, user: User) -> None:
        file = self.get(file_id, user, ROLE_EDITOR)
        file.is_deleted = True
        self.db.commit()
