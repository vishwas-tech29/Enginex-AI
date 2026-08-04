import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.cad.schemas import (
    AddArcRequest,
    AddAssemblyConstraintRequest,
    AddAssemblyPartRequest,
    AddCircleRequest,
    AddLineRequest,
    AddPointRequest,
    AddSketchConstraintRequest,
    AnimateConstraintRequest,
    BooleanRequest,
    CADObjectOut,
    ChamferRequest,
    CollisionsResponse,
    CreateAssemblyRequest,
    CreateBodyRequest,
    CreateSketchRequest,
    ExtrudeRequest,
    FilletRequest,
    MeshResponse,
    RevolveRequest,
    SolveSketchResponse,
    UpdateSketchRequest,
)
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


@router.post("/sketches/{sketch_id}/points")
def add_point(
    sketch_id: uuid.UUID,
    payload: AddPointRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).add_point(sketch_id, payload, current_user)


@router.post("/sketches/{sketch_id}/lines")
def add_line(
    sketch_id: uuid.UUID,
    payload: AddLineRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).add_line(sketch_id, payload, current_user)


@router.post("/sketches/{sketch_id}/circles")
def add_circle(
    sketch_id: uuid.UUID,
    payload: AddCircleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).add_circle(sketch_id, payload, current_user)


@router.post("/sketches/{sketch_id}/arcs")
def add_arc(
    sketch_id: uuid.UUID,
    payload: AddArcRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).add_arc(sketch_id, payload, current_user)


@router.post("/sketches/{sketch_id}/constraints")
def add_constraint(
    sketch_id: uuid.UUID,
    payload: AddSketchConstraintRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).add_sketch_constraint(sketch_id, payload, current_user)


@router.post("/sketches/{sketch_id}/solve", response_model=SolveSketchResponse)
def solve_sketch(
    sketch_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).solve_sketch(sketch_id, current_user)


@router.get("/bodies", response_model=list[CADObjectOut])
def list_bodies(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).list_bodies(file_id, current_user)


@router.post("/bodies", response_model=CADObjectOut, status_code=201)
def create_body(
    payload: CreateBodyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).create_body(payload, current_user)


@router.get("/bodies/{body_id}", response_model=CADObjectOut)
def get_body(
    body_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).get(body_id, current_user)


@router.post("/bodies/{body_id}/extrude", response_model=CADObjectOut)
def extrude(
    body_id: uuid.UUID,
    payload: ExtrudeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).extrude(body_id, payload, current_user)


@router.post("/bodies/{body_id}/revolve", response_model=CADObjectOut)
def revolve(
    body_id: uuid.UUID,
    payload: RevolveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).revolve(body_id, payload, current_user)


@router.post("/bodies/{body_id}/fillet", response_model=CADObjectOut)
def fillet(
    body_id: uuid.UUID,
    payload: FilletRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).fillet(body_id, payload, current_user)


@router.post("/bodies/{body_id}/chamfer", response_model=CADObjectOut)
def chamfer(
    body_id: uuid.UUID,
    payload: ChamferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).chamfer(body_id, payload, current_user)


@router.post("/bodies/{body_id}/boolean/union", response_model=CADObjectOut)
def boolean_union(
    body_id: uuid.UUID,
    payload: BooleanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).boolean_op(body_id, "boolean_union", payload, current_user)


@router.post("/bodies/{body_id}/boolean/cut", response_model=CADObjectOut)
def boolean_cut(
    body_id: uuid.UUID,
    payload: BooleanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).boolean_op(body_id, "boolean_cut", payload, current_user)


@router.post("/bodies/{body_id}/boolean/intersect", response_model=CADObjectOut)
def boolean_intersect(
    body_id: uuid.UUID,
    payload: BooleanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).boolean_op(body_id, "boolean_intersect", payload, current_user)


@router.get("/bodies/{body_id}/mesh", response_model=MeshResponse)
def get_mesh(
    body_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).get_mesh(body_id, current_user)


@router.get("/export/step/{body_id}")
def export_step(
    body_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content, media_type, filename = CADService(db).export_body(body_id, "step", current_user)
    return Response(
        content=content, media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/stl/{body_id}")
def export_stl(
    body_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content, media_type, filename = CADService(db).export_body(body_id, "stl", current_user)
    return Response(
        content=content, media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/obj/{body_id}")
def export_obj(
    body_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content, media_type, filename = CADService(db).export_body(body_id, "obj", current_user)
    return Response(
        content=content, media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/assemblies", response_model=CADObjectOut, status_code=201)
def create_assembly(
    payload: CreateAssemblyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).create_assembly(payload, current_user)


@router.get("/assemblies/{assembly_id}", response_model=CADObjectOut)
def get_assembly(
    assembly_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).get(assembly_id, current_user)


@router.post("/assemblies/{assembly_id}/parts")
def add_assembly_part(
    assembly_id: uuid.UUID,
    payload: AddAssemblyPartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).add_assembly_part(assembly_id, payload, current_user)


@router.post("/assemblies/{assembly_id}/constraints")
def add_assembly_constraint(
    assembly_id: uuid.UUID,
    payload: AddAssemblyConstraintRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).add_assembly_constraint(assembly_id, payload, current_user)


@router.post("/assemblies/{assembly_id}/constraints/{constraint_id}/animate")
def animate_assembly_constraint(
    assembly_id: uuid.UUID,
    constraint_id: str,
    payload: AnimateConstraintRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CADService(db).animate_assembly_constraint(assembly_id, constraint_id, payload.parameter, current_user)


@router.get("/assemblies/{assembly_id}/collisions", response_model=CollisionsResponse)
def get_assembly_collisions(
    assembly_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"collisions": CADService(db).get_assembly_collisions(assembly_id, current_user)}
