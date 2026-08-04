import uuid

from sqlalchemy.orm import Session

from app.api.v1.cad.schemas import (
    AddArcRequest,
    AddAssemblyConstraintRequest,
    AddAssemblyPartRequest,
    AddCircleRequest,
    AddLineRequest,
    AddPointRequest,
    AddSketchConstraintRequest,
    BooleanRequest,
    ChamferRequest,
    CreateAssemblyRequest,
    CreateBodyRequest,
    CreateSketchRequest,
    ExtrudeRequest,
    FilletRequest,
    RevolveRequest,
    UpdateSketchRequest,
)
from app.api.v1.files.service import FileService
from app.api.v1.projects.service import ROLE_EDITOR, ROLE_VIEWER
from app.cad.assembly.assembly_engine import (
    AssemblyDocument,
    AssemblyError,
    AssemblyMotionConstraint,
    PartInstance,
    animate_constraint,
    detect_collisions,
)
from app.cad.export.exporters import export_obj, export_step, export_stl, get_mesh
from app.cad.features.feature_ops import FeatureError, append_feature, rebuild_shape
from app.cad.sketch.constraints import SketchConstraint
from app.cad.sketch.entities import SketchArc, SketchCircle, SketchDocument, SketchLine, SketchPoint
from app.cad.sketch.solver import SketchSolver
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.cad_object import CADObject


class CADService:
    def __init__(self, db: Session):
        self.db = db
        self.files = FileService(db)

    # --- sketches (documents) -----------------------------------------

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

    # --- sketch geometry -------------------------------------------------

    def _save_sketch_doc(self, sketch: CADObject, doc: SketchDocument, user) -> CADObject:
        sketch.data = doc.to_dict()
        sketch.version_number += 1
        sketch.updated_by = user.id
        self.db.commit()
        self.db.refresh(sketch)
        return sketch

    def add_point(self, sketch_id: uuid.UUID, payload: AddPointRequest, user) -> dict:
        sketch = self.get(sketch_id, user, ROLE_EDITOR)
        doc = SketchDocument.from_dict(sketch.data)
        point_id = f"pt_{len(doc.points)}_{uuid.uuid4().hex[:6]}"
        doc.points[point_id] = SketchPoint(point_id, payload.x, payload.y, payload.fixed)
        self._save_sketch_doc(sketch, doc, user)
        return {"id": point_id, "x": payload.x, "y": payload.y, "fixed": payload.fixed}

    def add_line(self, sketch_id: uuid.UUID, payload: AddLineRequest, user) -> dict:
        sketch = self.get(sketch_id, user, ROLE_EDITOR)
        doc = SketchDocument.from_dict(sketch.data)
        if payload.start_id not in doc.points or payload.end_id not in doc.points:
            raise ValidationError("start_id/end_id", "referenced point does not exist in this sketch")
        line_id = f"ln_{len(doc.lines)}_{uuid.uuid4().hex[:6]}"
        doc.lines[line_id] = SketchLine(line_id, payload.start_id, payload.end_id)
        self._save_sketch_doc(sketch, doc, user)
        return {"id": line_id, "start_id": payload.start_id, "end_id": payload.end_id}

    def add_circle(self, sketch_id: uuid.UUID, payload: AddCircleRequest, user) -> dict:
        sketch = self.get(sketch_id, user, ROLE_EDITOR)
        doc = SketchDocument.from_dict(sketch.data)
        if payload.center_id not in doc.points:
            raise ValidationError("center_id", "referenced point does not exist in this sketch")
        circle_id = f"ci_{len(doc.circles)}_{uuid.uuid4().hex[:6]}"
        doc.circles[circle_id] = SketchCircle(circle_id, payload.center_id, payload.radius)
        self._save_sketch_doc(sketch, doc, user)
        return {"id": circle_id, "center_id": payload.center_id, "radius": payload.radius}

    def add_arc(self, sketch_id: uuid.UUID, payload: AddArcRequest, user) -> dict:
        sketch = self.get(sketch_id, user, ROLE_EDITOR)
        doc = SketchDocument.from_dict(sketch.data)
        if payload.center_id not in doc.points:
            raise ValidationError("center_id", "referenced point does not exist in this sketch")
        arc_id = f"ar_{len(doc.arcs)}_{uuid.uuid4().hex[:6]}"
        doc.arcs[arc_id] = SketchArc(
            arc_id, payload.center_id, payload.radius, payload.start_angle, payload.end_angle
        )
        self._save_sketch_doc(sketch, doc, user)
        return {"id": arc_id}

    def add_sketch_constraint(self, sketch_id: uuid.UUID, payload: AddSketchConstraintRequest, user) -> dict:
        sketch = self.get(sketch_id, user, ROLE_EDITOR)
        constraints = [SketchConstraint.from_dict(c) for c in sketch.data.get("constraints", [])]
        constraint_id = f"c_{len(constraints)}_{uuid.uuid4().hex[:6]}"
        new_constraint = SketchConstraint(constraint_id, payload.type, payload.entities, payload.value)
        constraints.append(new_constraint)

        # A fresh dict, not `sketch.data` mutated in place: SQLAlchemy's
        # change-tracking compares object identity/value on assignment, so
        # `sketch.data = sketch.data` (even after mutating it) can be seen
        # as a no-op and silently dropped on the next refresh().
        sketch.data = {**sketch.data, "constraints": [c.to_dict() for c in constraints]}
        sketch.version_number += 1
        sketch.updated_by = user.id
        self.db.commit()
        self.db.refresh(sketch)
        return new_constraint.to_dict()

    def solve_sketch(self, sketch_id: uuid.UUID, user) -> dict:
        sketch = self.get(sketch_id, user, ROLE_VIEWER)
        doc = SketchDocument.from_dict(sketch.data)
        constraints = [SketchConstraint.from_dict(c) for c in sketch.data.get("constraints", [])]
        result = SketchSolver(doc, constraints).solve()

        # Persist the solved geometry so subsequent reads/extrudes see it.
        sketch.data = {**doc.to_dict(), "constraints": [c.to_dict() for c in constraints]}
        self.db.commit()
        return result.to_dict()

    # --- bodies / features -------------------------------------------------

    def create_body(self, payload: CreateBodyRequest, user) -> CADObject:
        self.files.get(payload.file_id, user, ROLE_EDITOR)
        obj = CADObject(
            file_id=payload.file_id, object_type="body", name=payload.name,
            data={"features": []}, created_by=user.id, updated_by=user.id,
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def _append_feature(self, body_id: uuid.UUID, feature: dict, user) -> CADObject:
        body = self.get(body_id, user, ROLE_EDITOR)
        try:
            return append_feature(self.db, body, feature)
        except FeatureError as exc:
            raise ConflictError(str(exc)) from exc

    def extrude(self, body_id: uuid.UUID, payload: ExtrudeRequest, user) -> CADObject:
        self.get(payload.sketch_id, user, ROLE_VIEWER)  # sketch must be readable too
        return self._append_feature(
            body_id,
            {
                "type": "extrude", "sketch_id": str(payload.sketch_id),
                "distance": payload.distance, "symmetric": payload.symmetric,
            },
            user,
        )

    def revolve(self, body_id: uuid.UUID, payload: RevolveRequest, user) -> CADObject:
        self.get(payload.sketch_id, user, ROLE_VIEWER)
        return self._append_feature(
            body_id,
            {
                "type": "revolve", "sketch_id": str(payload.sketch_id), "angle": payload.angle,
                "axis_point": payload.axis_point, "axis_dir": payload.axis_dir,
            },
            user,
        )

    def fillet(self, body_id: uuid.UUID, payload: FilletRequest, user) -> CADObject:
        return self._append_feature(
            body_id, {"type": "fillet", "radius": payload.radius, "selector": payload.selector}, user
        )

    def chamfer(self, body_id: uuid.UUID, payload: ChamferRequest, user) -> CADObject:
        return self._append_feature(
            body_id, {"type": "chamfer", "distance": payload.distance, "selector": payload.selector}, user
        )

    def boolean_op(self, body_id: uuid.UUID, op_type: str, payload: BooleanRequest, user) -> CADObject:
        self.get(payload.other_body_id, user, ROLE_VIEWER)
        return self._append_feature(body_id, {"type": op_type, "other_body_id": str(payload.other_body_id)}, user)

    def get_mesh(self, body_id: uuid.UUID, user) -> dict:
        body = self.get(body_id, user, ROLE_VIEWER)
        try:
            shape = rebuild_shape(self.db, body)
        except FeatureError as exc:
            raise ConflictError(str(exc)) from exc
        return get_mesh(shape)

    def export_body(self, body_id: uuid.UUID, fmt: str, user) -> tuple[bytes, str, str]:
        body = self.get(body_id, user, ROLE_VIEWER)
        try:
            shape = rebuild_shape(self.db, body)
        except FeatureError as exc:
            raise ConflictError(str(exc)) from exc

        if fmt == "step":
            return export_step(shape), "model/step", f"{body.name}.step"
        if fmt == "stl":
            return export_stl(shape), "model/stl", f"{body.name}.stl"
        if fmt == "obj":
            return export_obj(shape).encode("utf-8"), "text/plain", f"{body.name}.obj"
        raise ValidationError("fmt", f"unsupported export format: {fmt}")

    # --- assemblies -------------------------------------------------

    def create_assembly(self, payload: CreateAssemblyRequest, user) -> CADObject:
        self.files.get(payload.file_id, user, ROLE_EDITOR)
        obj = CADObject(
            file_id=payload.file_id, object_type="assembly", name=payload.name,
            data=AssemblyDocument().to_dict(), created_by=user.id, updated_by=user.id,
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def add_assembly_part(self, assembly_id: uuid.UUID, payload: AddAssemblyPartRequest, user) -> dict:
        assembly = self.get(assembly_id, user, ROLE_EDITOR)
        self.get(payload.body_id, user, ROLE_VIEWER)  # body must exist & be readable
        doc = AssemblyDocument.from_dict(assembly.data)
        instance_id = f"inst_{len(doc.parts)}_{uuid.uuid4().hex[:6]}"
        part = PartInstance(instance_id, str(payload.body_id), payload.name, position=payload.position)
        doc.parts[instance_id] = part

        assembly.data = doc.to_dict()
        assembly.version_number += 1
        assembly.updated_by = user.id
        self.db.commit()
        return part.to_dict()

    def add_assembly_constraint(
        self, assembly_id: uuid.UUID, payload: AddAssemblyConstraintRequest, user
    ) -> dict:
        assembly = self.get(assembly_id, user, ROLE_EDITOR)
        doc = AssemblyDocument.from_dict(assembly.data)
        for pid in (payload.part1_instance_id, payload.part2_instance_id):
            if pid not in doc.parts:
                raise ValidationError("part_instance_id", f"unknown part instance: {pid}")

        constraint_id = f"mc_{len(doc.constraints)}_{uuid.uuid4().hex[:6]}"
        constraint = AssemblyMotionConstraint(
            constraint_id, payload.type, payload.part1_instance_id, payload.part2_instance_id,
            axis_point=payload.axis_point, axis_dir=payload.axis_dir,
        )
        doc.constraints[constraint_id] = constraint

        assembly.data = doc.to_dict()
        assembly.version_number += 1
        assembly.updated_by = user.id
        self.db.commit()
        return constraint.to_dict()

    def animate_assembly_constraint(self, assembly_id: uuid.UUID, constraint_id: str, parameter: float, user) -> dict:
        assembly = self.get(assembly_id, user, ROLE_EDITOR)
        doc = AssemblyDocument.from_dict(assembly.data)
        try:
            part = animate_constraint(doc, constraint_id, parameter)
        except AssemblyError as exc:
            raise ConflictError(str(exc)) from exc

        assembly.data = doc.to_dict()
        assembly.version_number += 1
        assembly.updated_by = user.id
        self.db.commit()
        return part.to_dict()

    def get_assembly_collisions(self, assembly_id: uuid.UUID, user) -> list[list[str]]:
        assembly = self.get(assembly_id, user, ROLE_VIEWER)
        doc = AssemblyDocument.from_dict(assembly.data)
        try:
            pairs = detect_collisions(self.db, doc)
        except (AssemblyError, FeatureError) as exc:
            raise ConflictError(str(exc)) from exc
        return [list(pair) for pair in pairs]
