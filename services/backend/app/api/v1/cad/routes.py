import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.cad.schemas import CADObjectOut, CreateSketchRequest, UpdateSketchRequest
from app.api.v1.cad.service import CADService
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/cad", tags=["CAD"])


@router.post("/sketches", response_model=CADObjectOut, status_code=201)
def create_sketch(
    payload: CreateSketchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).create_sketch(payload, current_user)


@router.get("/sketches/{sketch_id}", response_model=CADObjectOut)
def get_sketch(
    sketch_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).get(sketch_id, current_user)


@router.put("/sketches/{sketch_id}", response_model=CADObjectOut)
def update_sketch(
    sketch_id: uuid.UUID,
    payload: UpdateSketchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).update(sketch_id, payload, current_user)


@router.delete("/sketches/{sketch_id}", status_code=204)
def delete_sketch(
    sketch_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    CADService(db).delete(sketch_id, current_user)
    return None


@router.post("/sketches/{sketch_id}/constraints")
def add_constraint(
    sketch_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    CADService(db).add_constraint(sketch_id, current_user)


@router.get("/bodies", response_model=list[CADObjectOut])
def list_bodies(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).list_bodies(file_id, current_user)


@router.post("/bodies/{body_id}/extrude")
def extrude(
    body_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    CADService(db).feature_operation(body_id, "extrude", current_user)


@router.post("/bodies/{body_id}/revolve")
def revolve(
    body_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    CADService(db).feature_operation(body_id, "revolve", current_user)


@router.post("/bodies/{body_id}/fillet")
def fillet(
    body_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    CADService(db).feature_operation(body_id, "fillet", current_user)


@router.post("/bodies/{body_id}/chamfer")
def chamfer(
    body_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    CADService(db).feature_operation(body_id, "chamfer", current_user)


@router.get("/export/step/{body_id}")
def export_step(
    body_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    CADService(db).export(body_id, "STEP", current_user)


@router.get("/export/stl/{body_id}")
def export_stl(
    body_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    CADService(db).export(body_id, "STL", current_user)
