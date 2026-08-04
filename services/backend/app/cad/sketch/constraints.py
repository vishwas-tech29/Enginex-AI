import math
from dataclasses import dataclass

from app.cad.sketch.entities import SketchDocument

SUPPORTED_TYPES = {
    "horizontal",
    "vertical",
    "parallel",
    "perpendicular",
    "equal_length",
    "equal_radius",
    "distance",
    "length",
    "angle",
    "concentric",
    "tangent_line_circle",
    "coincident",
    "radius",
}


@dataclass
class SketchConstraint:
    id: str
    type: str
    entities: list[str]  # entity/point IDs, meaning depends on `type`
    value: float | None = None  # mm or degrees, depending on type

    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type, "entities": self.entities, "value": self.value}

    @staticmethod
    def from_dict(data: dict) -> "SketchConstraint":
        return SketchConstraint(
            id=data["id"], type=data["type"], entities=data["entities"], value=data.get("value")
        )


def residuals(doc: SketchDocument, c: SketchConstraint) -> list[float]:
    """Compute the residual(s) for one constraint against the current sketch
    state. A solved sketch drives every residual to ~0."""
    if c.type == "horizontal":
        line = doc.lines[c.entities[0]]
        return [doc.points[line.end_id].y - doc.points[line.start_id].y]

    if c.type == "vertical":
        line = doc.lines[c.entities[0]]
        return [doc.points[line.end_id].x - doc.points[line.start_id].x]

    if c.type == "parallel":
        d1 = doc.line_direction(c.entities[0])
        d2 = doc.line_direction(c.entities[1])
        return [d1[0] * d2[1] - d1[1] * d2[0]]  # cross product ~ 0

    if c.type == "perpendicular":
        d1 = doc.line_direction(c.entities[0])
        d2 = doc.line_direction(c.entities[1])
        return [d1[0] * d2[0] + d1[1] * d2[1]]  # dot product ~ 0

    if c.type == "equal_length":
        return [doc.line_length(c.entities[0]) - doc.line_length(c.entities[1])]

    if c.type == "equal_radius":
        r1 = _radius_of(doc, c.entities[0])
        r2 = _radius_of(doc, c.entities[1])
        return [r1 - r2]

    if c.type == "distance":
        p1, p2 = doc.points[c.entities[0]], doc.points[c.entities[1]]
        dist = math.hypot(p2.x - p1.x, p2.y - p1.y)
        return [dist - (c.value or 0)]

    if c.type == "length":
        return [doc.line_length(c.entities[0]) - (c.value or 0)]

    if c.type == "angle":
        d1 = doc.line_direction(c.entities[0])
        d2 = doc.line_direction(c.entities[1])
        angle = math.degrees(math.acos(max(-1.0, min(1.0, d1[0] * d2[0] + d1[1] * d2[1]))))
        return [angle - (c.value or 0)]

    if c.type == "concentric":
        p1 = doc.points[_center_of(doc, c.entities[0])]
        p2 = doc.points[_center_of(doc, c.entities[1])]
        return [p1.x - p2.x, p1.y - p2.y]

    if c.type == "tangent_line_circle":
        line_id, circle_id = c.entities[0], c.entities[1]
        line = doc.lines[line_id]
        p1, p2 = doc.points[line.start_id], doc.points[line.end_id]
        circle = doc.circles[circle_id]
        center = doc.points[circle.center_id]
        # point-to-line distance
        num = abs((p2.x - p1.x) * (p1.y - center.y) - (p1.x - center.x) * (p2.y - p1.y))
        den = math.hypot(p2.x - p1.x, p2.y - p1.y) or 1.0
        return [(num / den) - circle.radius]

    if c.type == "coincident":
        p1, p2 = doc.points[c.entities[0]], doc.points[c.entities[1]]
        return [p1.x - p2.x, p1.y - p2.y]

    if c.type == "radius":
        return [_radius_of(doc, c.entities[0]) - (c.value or 0)]

    raise ValueError(f"Unsupported constraint type: {c.type}")


def _radius_of(doc: SketchDocument, entity_id: str) -> float:
    if entity_id in doc.circles:
        return doc.circles[entity_id].radius
    return doc.arcs[entity_id].radius


def _center_of(doc: SketchDocument, entity_id: str) -> str:
    if entity_id in doc.circles:
        return doc.circles[entity_id].center_id
    return doc.arcs[entity_id].center_id
