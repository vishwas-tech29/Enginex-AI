import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.folders.schemas import (
    CreateFolderRequest,
    FolderOut,
    MoveFolderRequest,
    UpdateFolderRequest,
)
from app.api.v1.folders.service import FolderService
from app.database import get_db
from app.models.user import User

router = APIRouter(tags=["Folders"])


@router.get("/projects/{project_id}/folders", response_model=list[FolderOut])
def list_folders(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FolderService(db).list_for_project(project_id, current_user)


@router.post("/projects/{project_id}/folders", response_model=FolderOut, status_code=201)
def create_folder(
    project_id: uuid.UUID,
    payload: CreateFolderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FolderService(db).create(project_id, payload, current_user)


@router.get("/folders/{folder_id}", response_model=FolderOut)
def get_folder(
    folder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FolderService(db).get(folder_id, current_user)


@router.put("/folders/{folder_id}", response_model=FolderOut)
def update_folder(
    folder_id: uuid.UUID,
    payload: UpdateFolderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FolderService(db).update(folder_id, payload, current_user)


@router.delete("/folders/{folder_id}", status_code=204)
def delete_folder(
    folder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    FolderService(db).delete(folder_id, current_user)
    return None


@router.post("/folders/{folder_id}/move", response_model=FolderOut)
def move_folder(
    folder_id: uuid.UUID,
    payload: MoveFolderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FolderService(db).move(folder_id, payload, current_user)
