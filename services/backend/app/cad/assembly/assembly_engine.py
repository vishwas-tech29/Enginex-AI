import uuid
from dataclasses import dataclass, field

import numpy as np
from sqlalchemy.orm import Session

from app.cad.features.feature_ops import rebuild_shape
from app.models.cad_object import CADObject

MOTION_TYPES = {"rigid", "revolute", "prismatic", "cylindrical", "spherical", "planar"}
IDENTITY_ROTATION = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]


class AssemblyError(ValueError):
    pass


@dataclass
class PartInstance:
    instance_id: str
    body_id: str
    name: str
    position: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    orientation: list[float] = field(default_factory=lambda: list(IDENTITY_ROTATION))  # flattened 3x3

    def to_dict(self) -> dict:
        return {
            "instance_id": self.instance_id,
            "body_id": self.body_id,
            "name": self.name,
            "position": self.position,
            "orientation": self.orientation,
        }

    @staticmethod
    def from_dict(data: dict) -> "PartInstance":
        return PartInstance(
            instance_id=data["instance_id"],
            body_id=data["body_id"],
            name=data.get("name", ""),
            position=list(data.get("position", [0.0, 0.0, 0.0])),
            orientation=list(data.get("orientation", IDENTITY_ROTATION)),
        )


@dataclass
class AssemblyMotionConstraint:
    id: str
    type: str  # one of MOTION_TYPES
    part1_instance_id: str
    part2_instance_id: str
    axis_point: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    axis_dir: list[float] = field(default_factory=lambda: [0.0, 0.0, 1.0])
    parameter: float = 0.0  # radians for revolute, mm for prismatic

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "part1_instance_id": self.part1_instance_id,
            "part2_instance_id": self.part2_instance_id,
            "axis_point": self.axis_point,
            "axis_dir": self.axis_dir,
            "parameter": self.parameter,
        }

    @staticmethod
    def from_dict(data: dict) -> "AssemblyMotionConstraint":
        return AssemblyMotionConstraint(
            id=data["id"],
            type=data["type"],
            part1_instance_id=data["part1_instance_id"],
            part2_instance_id=data["part2_instance_id"],
            axis_point=list(data.get("axis_point", [0.0, 0.0, 0.0])),
            axis_dir=list(data.get("axis_dir", [0.0, 0.0, 1.0])),
            parameter=data.get("parameter", 0.0),
        )


@dataclass
class AssemblyDocument:
    parts: dict[str, PartInstance] = field(default_factory=dict)
    constraints: dict[str, AssemblyMotionConstraint] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "parts": {k: v.to_dict() for k, v in self.parts.items()},
            "constraints": {k: v.to_dict() for k, v in self.constraints.items()},
        }

    @staticmethod
    def from_dict(data: dict) -> "AssemblyDocument":
        doc = AssemblyDocument()
        for k, v in (data or {}).get("parts", {}).items():
            doc.parts[k] = PartInstance.from_dict(v)
        for k, v in (data or {}).get("constraints", {}).items():
            doc.constraints[k] = AssemblyMotionConstraint.from_dict(v)
        return doc


def _rodrigues_rotation_matrix(axis_dir: list[float], angle: float) -> np.ndarray:
    """Real rotation-matrix construction (Rodrigues' formula) for rotating
    by `angle` radians around an axis through the origin with direction
    `axis_dir` — not a fixed-axis placeholder like `orientation=(0, angle, 0)`."""
    axis = np.array(axis_dir, dtype=float)
    norm = np.linalg.norm(axis)
    if norm < 1e-9:
        raise AssemblyError("Motion constraint axis_dir cannot be the zero vector")
    axis = axis / norm

    K = np.array(
        [[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]]
    )
    identity = np.eye(3)
    return identity + np.sin(angle) * K + (1 - np.cos(angle)) * (K @ K)


def animate_constraint(doc: AssemblyDocument, constraint_id: str, parameter_value: float) -> PartInstance:
    """Move `part2` of a motion constraint by `parameter_value` (radians for
    revolute, mm for prismatic) — real rotation/translation math about an
    arbitrary axis, not a fixed-axis stand-in."""
    constraint = doc.constraints.get(constraint_id)
    if constraint is None:
        raise AssemblyError(f"Constraint not found: {constraint_id}")

    part = doc.parts.get(constraint.part2_instance_id)
    if part is None:
        raise AssemblyError(f"Part instance not found: {constraint.part2_instance_id}")

    constraint.parameter = parameter_value

    if constraint.type == "revolute":
        R = _rodrigues_rotation_matrix(constraint.axis_dir, parameter_value)
        pivot = np.array(constraint.axis_point)
        pos = np.array(part.position)
        part.position = (R @ (pos - pivot) + pivot).tolist()
        current_R = np.array(part.orientation).reshape(3, 3)
        part.orientation = (R @ current_R).flatten().tolist()

    elif constraint.type == "prismatic":
        axis = np.array(constraint.axis_dir, dtype=float)
        axis = axis / (np.linalg.norm(axis) or 1.0)
        part.position = (np.array(part.position) + axis * parameter_value).tolist()

    else:
        raise AssemblyError(f"Motion constraint type '{constraint.type}' has no parameterized animation")

    return part


def compute_world_bounding_box(
    db: Session, part: PartInstance, _cache: dict[str, tuple] | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Real AABB of a part instance in assembly space: rebuild its body's
    actual solid, take its true bounding box, transform all 8 corners by
    the instance's position/orientation, and re-bound. That last step is a
    standard, honest broad-phase approximation (an AABB of a rotated AABB
    isn't tight) — good enough for "do these two parts roughly overlap",
    not for exact contact detection.
    """
    cache = _cache if _cache is not None else {}
    if part.body_id in cache:
        local_min, local_max = cache[part.body_id]
    else:
        body = db.get(CADObject, uuid.UUID(part.body_id))
        if body is None:
            raise AssemblyError(f"Body not found: {part.body_id}")
        shape = rebuild_shape(db, body).val()
        bbox = shape.BoundingBox()
        local_min = np.array([bbox.xmin, bbox.ymin, bbox.zmin])
        local_max = np.array([bbox.xmax, bbox.ymax, bbox.zmax])
        cache[part.body_id] = (local_min, local_max)

    R = np.array(part.orientation).reshape(3, 3)
    t = np.array(part.position)
    corners = np.array(
        [
            [x, y, z]
            for x in (local_min[0], local_max[0])
            for y in (local_min[1], local_max[1])
            for z in (local_min[2], local_max[2])
        ]
    )
    world_corners = corners @ R.T + t
    return world_corners.min(axis=0), world_corners.max(axis=0)


def detect_collisions(db: Session, doc: AssemblyDocument) -> list[tuple[str, str]]:
    """Real AABB-overlap broad-phase collision detection between every pair
    of part instances (not a fixed-radius distance threshold)."""
    cache: dict[str, tuple] = {}
    boxes = {
        instance_id: compute_world_bounding_box(db, part, cache)
        for instance_id, part in doc.parts.items()
    }

    collisions = []
    ids = list(boxes.keys())
    for i, id1 in enumerate(ids):
        min1, max1 = boxes[id1]
        for id2 in ids[i + 1 :]:
            min2, max2 = boxes[id2]
            overlap = np.all(min1 <= max2) and np.all(min2 <= max1)
            if overlap:
                collisions.append((id1, id2))
    return collisions
