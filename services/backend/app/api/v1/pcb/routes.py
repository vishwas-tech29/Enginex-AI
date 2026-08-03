import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.components.schemas import (
    CreateFootprintRequest,
    CreateSymbolRequest,
    FootprintOut,
    SymbolOut,
)
from app.api.v1.components.service import ComponentService
from app.api.v1.pcb.schemas import (
    BoardOut,
    ComponentOut,
    CreateBoardRequest,
    CreateComponentRequest,
    UpdateBoardRequest,
    UpdateComponentRequest,
)
from app.api.v1.pcb.service import PCBService
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/pcb", tags=["PCB"])


@router.post("/boards", response_model=BoardOut, status_code=201)
def create_board(
    payload: CreateBoardRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PCBService(db).create_board(payload, current_user)


@router.get("/boards/{board_id}", response_model=BoardOut)
def get_board(
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PCBService(db).get_board(board_id, current_user)


@router.put("/boards/{board_id}", response_model=BoardOut)
def update_board(
    board_id: uuid.UUID,
    payload: UpdateBoardRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PCBService(db).update_board(board_id, payload, current_user)


@router.post("/components", response_model=ComponentOut, status_code=201)
def create_component(
    payload: CreateComponentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PCBService(db).create_component(payload, current_user)


@router.get("/components/{component_id}", response_model=ComponentOut)
def get_component(
    component_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PCBService(db).get_component(component_id, current_user)


@router.put("/components/{component_id}", response_model=ComponentOut)
def update_component(
    component_id: uuid.UUID,
    payload: UpdateComponentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PCBService(db).update_component(component_id, payload, current_user)


@router.delete("/components/{component_id}", status_code=204)
def delete_component(
    component_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    PCBService(db).delete_component(component_id, current_user)
    return None


@router.post("/boards/{board_id}/drc")
def run_drc(
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    PCBService(db).run_drc(board_id, current_user)


@router.post("/boards/{board_id}/erc")
def run_erc(
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    PCBService(db).run_erc(board_id, current_user)


@router.get("/export/gerber/{board_id}")
def export_gerber(
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    PCBService(db).export(board_id, "Gerber", current_user)


@router.get("/export/bom/{board_id}")
def export_bom(
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    PCBService(db).export(board_id, "BOM", current_user)


# Thin aliases onto the shared component library (see /api/v1/symbols,
# /api/v1/footprints) so the PCB-scoped paths from the API spec resolve too.
@router.get("/libraries/symbols", response_model=list[SymbolOut])
def list_library_symbols(
    library: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ComponentService(db).list_symbols(library)


@router.post("/libraries/symbols", response_model=SymbolOut, status_code=201)
def create_library_symbol(
    payload: CreateSymbolRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ComponentService(db).create_symbol(payload)


@router.get("/libraries/footprints", response_model=list[FootprintOut])
def list_library_footprints(
    package_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ComponentService(db).list_footprints(package_type)


@router.post("/libraries/footprints", response_model=FootprintOut, status_code=201)
def create_library_footprint(
    payload: CreateFootprintRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ComponentService(db).create_footprint(payload)
