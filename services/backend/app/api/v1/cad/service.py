import uuid

from sqlalchemy.orm import Session

from app.api.v1.cad.schemas import CreateSketchRequest, UpdateSketchRequest
from app.api.v1.files.service import FileService
from app.api.v1.projects.service import ROLE_EDITOR, ROLE_VIEWER
from app.core.exceptions import EngineNotImplementedError, NotFoundError
from app.models.cad_object import CADObject


class CADService:
    """Persistence for CAD sketch/body records.

    Feature operations (extrude, revolve, fillet, chamfer) and exports
    (STEP/STL) need an actual geometry kernel, which is Phase 5 work — those
    raise `EngineNotImplementedError` (501) rather than faking a result.
    """

    def __init__(self, db: Session):
        self.db = db
        self.files = FileService(db)

    def create_sketch(self, payload: CreateSketchRequest, user) -> CADObject:
        self.files.get(payload.file_id, user, ROLE_EDITOR)
        obj = CADObject(
            file_id=payload.file_id,
            object_type="sketch",
            name=payload.name,
            data=payload.data,
            created_by=user.id,
            updated_by=user.id,
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get(self, cad_object_id: uuid.UUID, user, min_role: str = ROLE_VIEWER) -> CADObject:
        obj = self.db.get(CADObject, cad_object_id)
        if not obj:
            raise NotFoundError("CAD object", cad_object_id)
        self.files.get(obj.file_id, user, min_role)
        return obj

    def update(self, cad_object_id: uuid.UUID, payload: UpdateSketchRequest, user) -> CADObject:
        obj = self.get(cad_object_id, user, ROLE_EDITOR)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        obj.version_number += 1
        obj.updated_by = user.id
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, cad_object_id: uuid.UUID, user) -> None:
        obj = self.get(cad_object_id, user, ROLE_EDITOR)
        self.db.delete(obj)
        self.db.commit()

    def list_bodies(self, file_id: uuid.UUID, user) -> list[CADObject]:
        self.files.get(file_id, user, ROLE_VIEWER)
        return (
            self.db.query(CADObject)
            .filter(CADObject.file_id == file_id, CADObject.object_type == "body")
            .all()
        )

    def add_constraint(self, sketch_id: uuid.UUID, user) -> None:
        self.get(sketch_id, user, ROLE_EDITOR)
        raise EngineNotImplementedError("sketch constraints")

    def feature_operation(self, body_id: uuid.UUID, operation: str, user) -> None:
        self.get(body_id, user, ROLE_EDITOR)
        raise EngineNotImplementedError(operation)

    def export(self, body_id: uuid.UUID, fmt: str, user) -> None:
        self.get(body_id, user, ROLE_VIEWER)
        raise EngineNotImplementedError(f"export to {fmt}")
