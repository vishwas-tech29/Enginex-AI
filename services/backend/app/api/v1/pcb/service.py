import uuid

from sqlalchemy.orm import Session

from app.api.v1.files.service import FileService
from app.api.v1.pcb.schemas import (
    CreateBoardRequest,
    CreateComponentRequest,
    UpdateBoardRequest,
    UpdateComponentRequest,
)
from app.api.v1.projects.service import ROLE_EDITOR, ROLE_VIEWER
from app.core.exceptions import EngineNotImplementedError, NotFoundError
from app.models.pcb_board import PCBBoard, PCBComponent


class PCBService:
    """Persistence for PCB board/component records.

    DRC/ERC and Gerber/BOM export need a real routing/rules engine (Phase 6
    per docs/architecture/roadmap.md) — those raise `EngineNotImplementedError`.
    """

    def __init__(self, db: Session):
        self.db = db
        self.files = FileService(db)

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

    def update_board(self, board_id: uuid.UUID, payload: UpdateBoardRequest, user) -> PCBBoard:
        board = self.get_board(board_id, user, ROLE_EDITOR)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(board, field, value)
        self.db.commit()
        self.db.refresh(board)
        return board

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

    def run_drc(self, board_id: uuid.UUID, user) -> None:
        self.get_board(board_id, user, ROLE_VIEWER)
        raise EngineNotImplementedError("design rule check (DRC)")

    def run_erc(self, board_id: uuid.UUID, user) -> None:
        self.get_board(board_id, user, ROLE_VIEWER)
        raise EngineNotImplementedError("electrical rule check (ERC)")

    def export(self, board_id: uuid.UUID, fmt: str, user) -> None:
        self.get_board(board_id, user, ROLE_VIEWER)
        raise EngineNotImplementedError(f"export {fmt}")
