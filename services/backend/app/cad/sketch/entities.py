import math
from dataclasses import asdict, dataclass, field


@dataclass
class SketchPoint:
    id: str
    x: float
    y: float
    fixed: bool = False


@dataclass
class SketchLine:
    id: str
    start_id: str
    end_id: str


@dataclass
class SketchCircle:
    id: str
    center_id: str
    radius: float


@dataclass
class SketchArc:
    id: str
    center_id: str
    radius: float
    start_angle: float  # radians
    end_angle: float


@dataclass
class SketchDocument:
    """The full editable state of one sketch: points + curves built on them."""

    points: dict[str, SketchPoint] = field(default_factory=dict)
    lines: dict[str, SketchLine] = field(default_factory=dict)
    circles: dict[str, SketchCircle] = field(default_factory=dict)
    arcs: dict[str, SketchArc] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "points": {k: asdict(v) for k, v in self.points.items()},
            "lines": {k: asdict(v) for k, v in self.lines.items()},
            "circles": {k: asdict(v) for k, v in self.circles.items()},
            "arcs": {k: asdict(v) for k, v in self.arcs.items()},
        }

    @staticmethod
    def from_dict(data: dict) -> "SketchDocument":
        doc = SketchDocument()
        for k, v in (data or {}).get("points", {}).items():
            doc.points[k] = SketchPoint(**v)
        for k, v in (data or {}).get("lines", {}).items():
            doc.lines[k] = SketchLine(**v)
        for k, v in (data or {}).get("circles", {}).items():
            doc.circles[k] = SketchCircle(**v)
        for k, v in (data or {}).get("arcs", {}).items():
            doc.arcs[k] = SketchArc(**v)
        return doc

    def line_length(self, line_id: str) -> float:
        line = self.lines[line_id]
        p1, p2 = self.points[line.start_id], self.points[line.end_id]
        return math.hypot(p2.x - p1.x, p2.y - p1.y)

    def line_direction(self, line_id: str) -> tuple[float, float]:
        line = self.lines[line_id]
        p1, p2 = self.points[line.start_id], self.points[line.end_id]
        dx, dy = p2.x - p1.x, p2.y - p1.y
        norm = math.hypot(dx, dy) or 1.0
        return dx / norm, dy / norm
