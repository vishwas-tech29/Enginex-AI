import uuid

from fastapi import APIRouter, Depends, File as FileUpload, Form, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.files.schemas import FileOut, FileVersionOut
from app.api.v1.files.service import FileService
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload", response_model=FileOut, status_code=201)
def upload_file(
    project_id: uuid.UUID = Form(...),
    folder_id: uuid.UUID | None = Form(default=None),
    file: UploadFile = FileUpload(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FileService(db).upload(project_id, folder_id, file.filename, file.file, current_user)


@router.get("/{file_id}", response_model=FileOut)
def get_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FileService(db).get(file_id, current_user)


@router.get("/{file_id}/download")
def download_file(
    file_id: uuid.UUID,
    version_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target, filename = FileService(db).get_download_target(file_id, current_user, version_id)
    if target.kind == "url":
        return RedirectResponse(url=target.value)
    return FileResponse(path=target.value, filename=filename)


@router.get("/{file_id}/versions", response_model=list[FileVersionOut])
def list_versions(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FileService(db).list_versions(file_id, current_user)


@router.post("/{file_id}/revert-to/{version_id}", response_model=FileOut)
def revert_to_version(
    file_id: uuid.UUID,
    version_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FileService(db).revert_to_version(file_id, version_id, current_user)


@router.delete("/{file_id}", status_code=204)
def delete_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    FileService(db).delete(file_id, current_user)
    return None
