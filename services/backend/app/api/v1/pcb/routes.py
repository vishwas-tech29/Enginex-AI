import uuid

from fastapi import APIRouter, Depends, Response
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
    AddTraceRequest,
    AddViaRequest,
    AutoRouteRequest,
    AutoRouteResponse,
    BoardOut,
    ComponentOut,
    CreateBoardRequest,
    CreateComponentRequest,
    DRCResponse,
    ERCResponse,
    OptimizeTracesRequest,
    OptimizeTracesResponse,
    PCBMeshResponse,
    TraceOut,
    UpdateBoardRequest,
    UpdateComponentRequest,
    ViaOut,
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


@router.get("/boards", response_model=list[BoardOut])
def list_boards(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PCBService(db).list_boards(file_id, current_user)


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


@router.get("/components", response_model=list[ComponentOut])
def list_components(
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PCBService(db).list_components(board_id, current_user)


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


# --- Routing -------------------------------------------------


@router.post("/boards/{board_id}/traces", response_model=TraceOut, status_code=201)
def add_trace(
    board_id: uuid.UUID,
    payload: AddTraceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PCBService(db).add_trace(board_id, payload, current_user)


@router.post("/boards/{board_id}/vias", response_model=ViaOut, status_code=201)
def add_via(
    board_id: uuid.UUID,
    payload: AddViaRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PCBService(db).add_via(board_id, payload, current_user)


@router.post("/boards/{board_id}/auto-route", response_model=AutoRouteResponse)
def auto_route(
    board_id: uuid.UUID,
    payload: AutoRouteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    traces = PCBService(db).auto_route(board_id, payload, current_user)
    return {"traces": traces}


@router.post("/boards/{board_id}/optimize-traces", response_model=OptimizeTracesResponse)
def optimize_traces(
    board_id: uuid.UUID,
    payload: OptimizeTracesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    removed = PCBService(db).optimize_traces(board_id, payload.net, current_user)
    return {"removed": removed}


@router.get("/boards/{board_id}/mesh", response_model=PCBMeshResponse)
def get_mesh(
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PCBService(db).get_mesh(board_id, current_user)


# --- DRC / ERC -------------------------------------------------


@router.post("/boards/{board_id}/drc", response_model=DRCResponse)
def run_drc(
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    violations = PCBService(db).run_drc(board_id, current_user)
    return {"violations": violations}


@router.post("/boards/{board_id}/erc", response_model=ERCResponse)
def run_erc(
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    violations = PCBService(db).run_erc(board_id, current_user)
    return {"violations": violations}


# --- Export -------------------------------------------------


def _export_response(db: Session, board_id: uuid.UUID, fmt: str, current_user: User) -> Response:
    content, media_type, filename = PCBService(db).export(board_id, fmt, current_user)
    return Response(
        content=content, media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/gerber/{board_id}")
def export_gerber(
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _export_response(db, board_id, "gerber", current_user)


@router.get("/export/drill/{board_id}")
def export_drill(
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _export_response(db, board_id, "drill", current_user)


@router.get("/export/netlist/{board_id}")
def export_netlist(
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _export_response(db, board_id, "netlist", current_user)


@router.get("/export/bom/{board_id}")
def export_bom(
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _export_response(db, board_id, "bom", current_user)


@router.get("/export/step/{board_id}")
def export_step(
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _export_response(db, board_id, "step", current_user)


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
