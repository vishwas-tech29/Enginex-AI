import uuid

import cadquery as cq
from sqlalchemy.orm import Session

from app.cad.kernel.builder import build_profile_from_sketch
from app.cad.sketch.entities import SketchDocument
from app.models.cad_object import CADObject

BOOLEAN_TYPES = {"boolean_union", "boolean_cut", "boolean_intersect"}
MODIFIER_TYPES = {"fillet", "chamfer"} | BOOLEAN_TYPES
BASE_TYPES = {"extrude", "revolve"}
SUPPORTED_FEATURE_TYPES = BASE_TYPES | MODIFIER_TYPES


class FeatureError(ValueError):
    """A feature operation couldn't be applied — bad params or geometry."""


def _get_body(db: Session, body_id: str) -> CADObject:
    obj = db.get(CADObject, uuid.UUID(body_id))
    if obj is None:
        raise FeatureError(f"CAD object not found: {body_id}")
    return obj


def rebuild_shape(db: Session, body: CADObject, _visited: frozenset[uuid.UUID] | None = None) -> cq.Workplane:
    """Replay a body's feature history into a live CadQuery shape.

    This is the whole point of storing features as a JSON history rather
    than a serialized solid: the shape is always rebuilt from the
    parametric recipe, so editing an early feature's parameters and
    rebuilding genuinely re-derives every downstream feature — real
    parametric modeling, not a cached mesh with a fresh coat of paint.
    """
    _visited = (_visited or frozenset()) | {body.id}

    shape: cq.Workplane | None = None
    for op in body.data.get("features", []):
        op_type = op["type"]

        try:
            if op_type == "extrude":
                sketch = _get_body(db, op["sketch_id"])
                profile = build_profile_from_sketch(SketchDocument.from_dict(sketch.data))
                piece = profile.extrude(op["distance"], both=bool(op.get("symmetric", False)))
                shape = piece if shape is None else shape.union(piece)

            elif op_type == "revolve":
                sketch = _get_body(db, op["sketch_id"])
                profile = build_profile_from_sketch(SketchDocument.from_dict(sketch.data))
                axis_point = tuple(op.get("axis_point", [0, 0, 0]))
                axis_dir = tuple(op.get("axis_dir", [0, 1, 0]))
                piece = profile.revolve(op.get("angle", 360), axis_point, axis_dir)
                shape = piece if shape is None else shape.union(piece)

            elif op_type == "fillet":
                if shape is None:
                    raise FeatureError("Cannot fillet a body with no solid yet")
                selector = op.get("selector")
                edges = shape.edges(selector) if selector else shape.edges()
                shape = edges.fillet(op["radius"])

            elif op_type == "chamfer":
                if shape is None:
                    raise FeatureError("Cannot chamfer a body with no solid yet")
                selector = op.get("selector")
                edges = shape.edges(selector) if selector else shape.edges()
                shape = edges.chamfer(op["distance"])

            elif op_type in BOOLEAN_TYPES:
                if shape is None:
                    raise FeatureError(f"Cannot apply {op_type} to a body with no solid yet")
                other_id = uuid.UUID(op["other_body_id"])
                if other_id in _visited:
                    raise FeatureError("Circular body reference in boolean operation")
                other_body = _get_body(db, op["other_body_id"])
                other_shape = rebuild_shape(db, other_body, _visited)
                if op_type == "boolean_union":
                    shape = shape.union(other_shape)
                elif op_type == "boolean_cut":
                    shape = shape.cut(other_shape)
                else:
                    shape = shape.intersect(other_shape)

            else:
                raise FeatureError(f"Unknown feature type: {op_type}")

        except FeatureError:
            raise
        except Exception as exc:  # noqa: BLE001 — OCCT raises its own native
            # exception types (Standard_Failure etc.); normalize all of them
            # to FeatureError so callers get one catchable error type.
            raise FeatureError(f"Feature '{op_type}' failed: {exc}") from exc

    if shape is None:
        raise FeatureError("Body has no features yet")
    return shape


def append_feature(db: Session, body: CADObject, feature: dict) -> CADObject:
    """Append one feature to a body's history, validating it actually
    builds before persisting — an invalid feature never corrupts the
    stored history."""
    if feature["type"] not in SUPPORTED_FEATURE_TYPES:
        raise FeatureError(f"Unsupported feature type: {feature['type']}")

    candidate_features = [*body.data.get("features", []), feature]
    candidate_body = CADObject(
        id=body.id, file_id=body.file_id, object_type=body.object_type, name=body.name,
        data={"features": candidate_features},
    )
    rebuild_shape(db, candidate_body)  # raises FeatureError if invalid — nothing persisted yet

    body.data = {"features": candidate_features}
    body.version_number += 1
    db.commit()
    db.refresh(body)
    return body
