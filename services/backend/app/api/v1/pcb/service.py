import uuid

from sqlalchemy.orm import Session

from app.api.v1.components.service import ComponentService
from app.api.v1.files.service import FileService
from app.api.v1.pcb.schemas import (
    AddTraceRequest,
    AddViaRequest,
    AutoRouteRequest,
    CreateBoardRequest,
    CreateComponentRequest,
    UpdateBoardRequest,
    UpdateComponentRequest,
)
from app.api.v1.projects.service import ROLE_EDITOR, ROLE_VIEWER
from app.cad.export.exporters import export_step, get_mesh
from app.core.exceptions import NotFoundError, ValidationError
from app.models.pcb_board import PCBBoard, PCBComponent
from app.pcb.drc.drc_engine import run_drc as check_drc
from app.pcb.erc.erc_engine import run_erc as check_erc
from app.pcb.export.exporters import BOMExporter, GerberExporter, NCDrillExporter, NetlistExporter, build_board_shape
from app.pcb.layers import LayerType
from app.pcb.layout import PCBLayoutDocument, Point
from app.pcb.routing.routing_engine import (
    add_manual_trace,
    add_via as add_via_segment,
    auto_route_board,
    optimize_traces as optimize_net_traces,
)


def _parse_layer(value: str) -> LayerType:
    try:
        return LayerType(value)
    except ValueError as exc:
        raise ValidationError("layer", f"unknown layer: {value}") from exc


class PCBService:
    """Persistence for PCB boards/components, plus the routing/DRC/ERC/
    export engines under app.pcb — those are pure functions over an
    in-memory PCBLayoutDocument, this class is what round-trips that
    document through PCBBoard.data (a JSON column), the same pattern
    CADService uses for CADObject.data."""

    def __init__(self, db: Session):
        self.db = db
        self.files = FileService(db)
        self.library = ComponentService(db)

    # --- boards -------------------------------------------------

    def create_board(self, payload: CreateBoardRequest, user) -> PCBBoard:
        self.files.get(payload.file_id, user, ROLE_EDITOR)
        board = PCBBoard(
            file_id=payload.file_id,
            name=payload.name,
            width_mm=payload.width_mm,
            height_mm=payload.height_mm,
            layers_count=payload.layers_count,
        )
        self.db.add(board)
        self.db.commit()
        self.db.refresh(board)
        return board

    def get_board(self, board_id: uuid.UUID, user, min_role: str = ROLE_VIEWER) -> PCBBoard:
        board = self.db.get(PCBBoard, board_id)
        if not board:
            raise NotFoundError("PCB board", board_id)
        self.files.get(board.file_id, user, min_role)
        return board

    def list_boards(self, file_id: uuid.UUID, user) -> list[PCBBoard]:
        self.files.get(file_id, user, ROLE_VIEWER)
        return self.db.query(PCBBoard).filter(PCBBoard.file_id == file_id).all()

    def update_board(self, board_id: uuid.UUID, payload: UpdateBoardRequest, user) -> PCBBoard:
        board = self.get_board(board_id, user, ROLE_EDITOR)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(board, field, value)
        self.db.commit()
        self.db.refresh(board)
        return board

    # --- components -------------------------------------------------

    def create_component(self, payload: CreateComponentRequest, user) -> PCBComponent:
        self.get_board(payload.board_id, user, ROLE_EDITOR)
        component = PCBComponent(
            board_id=payload.board_id,
            reference_designator=payload.reference_designator,
            footprint_id=payload.footprint_id,
            library_entry_id=payload.library_entry_id,
            position_x=payload.position_x,
            position_y=payload.position_y,
            rotation_degrees=payload.rotation_degrees,
            data=payload.data,
        )
        self.db.add(component)
        self.db.commit()
        self.db.refresh(component)
        return component

    def list_components(self, board_id: uuid.UUID, user) -> list[PCBComponent]:
        self.get_board(board_id, user, ROLE_VIEWER)
        return self._components_for_board(board_id)

    def get_component(self, component_id: uuid.UUID, user) -> PCBComponent:
        component = self.db.get(PCBComponent, component_id)
        if not component:
            raise NotFoundError("PCB component", component_id)
        self.get_board(component.board_id, user, ROLE_VIEWER)
        return component

    def update_component(
        self, component_id: uuid.UUID, payload: UpdateComponentRequest, user
    ) -> PCBComponent:
        component = self.get_component(component_id, user)
        self.get_board(component.board_id, user, ROLE_EDITOR)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(component, field, value)
        self.db.commit()
        self.db.refresh(component)
        return component

    def delete_component(self, component_id: uuid.UUID, user) -> None:
        component = self.get_component(component_id, user)
        self.get_board(component.board_id, user, ROLE_EDITOR)
        self.db.delete(component)
        self.db.commit()

    # --- engine input helpers -------------------------------------------------

    def _components_for_board(self, board_id: uuid.UUID) -> list[PCBComponent]:
        return self.db.query(PCBComponent).filter(PCBComponent.board_id == board_id).all()

    def _footprints_for(self, components: list[PCBComponent]) -> dict[str, object]:
        return self.library.get_footprints_by_ids([c.footprint_id for c in components])

    def _library_components_for(self, components: list[PCBComponent]) -> dict[str, object]:
        return self.library.get_components_by_ids([c.library_entry_id for c in components])

    def _layout_doc(self, board: PCBBoard) -> PCBLayoutDocument:
        return PCBLayoutDocument.from_dict(board.data)

    def _save_layout_doc(self, board: PCBBoard, doc: PCBLayoutDocument) -> None:
        # A fresh dict, not `board.data` mutated in place — see the same
        # note in CADService._save_sketch_doc for why that matters for
        # SQLAlchemy's change tracking on a JSON column.
        board.data = {**board.data, **doc.to_dict()}
        self.db.commit()
        self.db.refresh(board)

    # --- routing -------------------------------------------------

    def add_trace(self, board_id: uuid.UUID, payload: AddTraceRequest, user) -> dict:
        board = self.get_board(board_id, user, ROLE_EDITOR)
        doc = self._layout_doc(board)
        segment_id = f"trace_{len(doc.traces)}_{uuid.uuid4().hex[:6]}"
        trace = add_manual_trace(
            doc,
            segment_id,
            Point(payload.start.x, payload.start.y),
            Point(payload.end.x, payload.end.y),
            _parse_layer(payload.layer),
            payload.net,
            payload.width,
        )
        self._save_layout_doc(board, doc)
        return trace.to_dict()

    def add_via(self, board_id: uuid.UUID, payload: AddViaRequest, user) -> dict:
        board = self.get_board(board_id, user, ROLE_EDITOR)
        doc = self._layout_doc(board)
        via_id = f"via_{len(doc.vias)}_{uuid.uuid4().hex[:6]}"
        via = add_via_segment(
            doc,
            via_id,
            Point(payload.position.x, payload.position.y),
            _parse_layer(payload.from_layer),
            _parse_layer(payload.to_layer),
            payload.net,
            payload.pad_diameter,
            payload.drill_diameter,
        )
        self._save_layout_doc(board, doc)
        return via.to_dict()

    def auto_route(self, board_id: uuid.UUID, payload: AutoRouteRequest, user) -> list[dict]:
        board = self.get_board(board_id, user, ROLE_EDITOR)
        doc = self._layout_doc(board)
        components = self._components_for_board(board_id)
        footprints = self._footprints_for(components)
        new_traces = auto_route_board(
            doc, board.width_mm, board.height_mm, components, footprints, _parse_layer(payload.layer)
        )
        self._save_layout_doc(board, doc)
        return [t.to_dict() for t in new_traces]

    def optimize_traces(self, board_id: uuid.UUID, net: str, user) -> int:
        board = self.get_board(board_id, user, ROLE_EDITOR)
        doc = self._layout_doc(board)
        removed = optimize_net_traces(doc, net)
        self._save_layout_doc(board, doc)
        return removed

    # --- DRC / ERC -------------------------------------------------

    def run_drc(self, board_id: uuid.UUID, user) -> list[dict]:
        board = self.get_board(board_id, user, ROLE_VIEWER)
        doc = self._layout_doc(board)
        components = self._components_for_board(board_id)
        footprints = self._footprints_for(components)
        return [v.to_dict() for v in check_drc(doc, components, footprints)]

    def run_erc(self, board_id: uuid.UUID, user) -> list[dict]:
        board = self.get_board(board_id, user, ROLE_VIEWER)
        doc = self._layout_doc(board)
        components = self._components_for_board(board_id)
        footprints = self._footprints_for(components)
        library_components = self._library_components_for(components)
        return [v.to_dict() for v in check_erc(doc, components, footprints, library_components)]

    # --- export -------------------------------------------------

    def export(self, board_id: uuid.UUID, fmt: str, user) -> tuple[bytes, str, str]:
        board = self.get_board(board_id, user, ROLE_VIEWER)
        components = self._components_for_board(board_id)
        footprints = self._footprints_for(components)
        doc = self._layout_doc(board)

        if fmt == "gerber":
            content = GerberExporter().export_copper_layer(components, footprints, doc, LayerType.TOP_COPPER)
            return content.encode("utf-8"), "text/plain", f"{board.name}_top_copper.gbr"
        if fmt == "drill":
            content = NCDrillExporter().export(components, footprints, doc)
            return content.encode("utf-8"), "text/plain", f"{board.name}.drl"
        if fmt == "netlist":
            content = NetlistExporter().export(board.name, components)
            return content.encode("utf-8"), "text/plain", f"{board.name}.net"
        if fmt == "bom":
            library_components = self._library_components_for(components)
            content = BOMExporter().export(components, library_components)
            return content.encode("utf-8"), "text/csv", f"{board.name}_bom.csv"
        if fmt == "step":
            shape = build_board_shape(board.width_mm, board.height_mm)
            return export_step(shape), "model/step", f"{board.name}.step"
        raise ValidationError("fmt", f"unsupported export format: {fmt}")

    def get_mesh(self, board_id: uuid.UUID, user) -> dict:
        board = self.get_board(board_id, user, ROLE_VIEWER)
        shape = build_board_shape(board.width_mm, board.height_mm)
        return get_mesh(shape)
