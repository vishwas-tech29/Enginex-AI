"""In-memory PCB layout document: the routing/DRC/ERC/export engines all
operate on this, the same way app.cad.sketch.entities.SketchDocument is the
shared in-memory shape for the sketch solver and kernel builder. The API
service layer round-trips it through PCBBoard.data (a JSON column) via
to_dict()/from_dict() — no dedicated tables, matching how sketches/assemblies
already persist.
"""

import math
from dataclasses import dataclass, field

from app.pcb.layers import LayerType

# Defaults per IPC-2221 class-2 style guidance (10 mil / 0.254mm), matching
# app.pcb.models.board's original constants.
DEFAULT_MIN_TRACE_WIDTH_MM = 0.254
DEFAULT_MIN_CLEARANCE_MM = 0.254
DEFAULT_MIN_VIA_PAD_DIA_MM = 0.76
DEFAULT_MIN_VIA_DRILL_DIA_MM = 0.33


@dataclass
class Point:
    x: float
    y: float

    def distance_to(self, other: "Point") -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y}

    @staticmethod
    def from_dict(data: dict) -> "Point":
        return Point(float(data["x"]), float(data["y"]))


@dataclass
class TraceSegment:
    segment_id: str
    layer: LayerType
    start: Point
    end: Point
    width: float
    net: str

    def length(self) -> float:
        return self.start.distance_to(self.end)

    def to_dict(self) -> dict:
        return {
            "id": self.segment_id,
            "layer": self.layer.value,
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "width": self.width,
            "net": self.net,
        }

    @staticmethod
    def from_dict(data: dict) -> "TraceSegment":
        return TraceSegment(
            data["id"],
            LayerType(data["layer"]),
            Point.from_dict(data["start"]),
            Point.from_dict(data["end"]),
            float(data["width"]),
            data["net"],
        )


@dataclass
class Via:
    via_id: str
    position: Point
    pad_diameter: float
    drill_diameter: float
    from_layer: LayerType
    to_layer: LayerType
    net: str

    def to_dict(self) -> dict:
        return {
            "id": self.via_id,
            "position": self.position.to_dict(),
            "pad_dia": self.pad_diameter,
            "drill_dia": self.drill_diameter,
            "from_layer": self.from_layer.value,
            "to_layer": self.to_layer.value,
            "net": self.net,
        }

    @staticmethod
    def from_dict(data: dict) -> "Via":
        return Via(
            data["id"],
            Point.from_dict(data["position"]),
            float(data["pad_dia"]),
            float(data["drill_dia"]),
            LayerType(data["from_layer"]),
            LayerType(data["to_layer"]),
            data["net"],
        )


@dataclass
class DesignRules:
    min_trace_width: float = DEFAULT_MIN_TRACE_WIDTH_MM
    min_clearance: float = DEFAULT_MIN_CLEARANCE_MM
    min_via_pad_dia: float = DEFAULT_MIN_VIA_PAD_DIA_MM
    min_via_drill_dia: float = DEFAULT_MIN_VIA_DRILL_DIA_MM

    def to_dict(self) -> dict:
        return {
            "min_trace_width": self.min_trace_width,
            "min_clearance": self.min_clearance,
            "min_via_pad_dia": self.min_via_pad_dia,
            "min_via_drill_dia": self.min_via_drill_dia,
        }

    @staticmethod
    def from_dict(data: dict) -> "DesignRules":
        defaults = DesignRules()
        return DesignRules(
            min_trace_width=float(data.get("min_trace_width", defaults.min_trace_width)),
            min_clearance=float(data.get("min_clearance", defaults.min_clearance)),
            min_via_pad_dia=float(data.get("min_via_pad_dia", defaults.min_via_pad_dia)),
            min_via_drill_dia=float(data.get("min_via_drill_dia", defaults.min_via_drill_dia)),
        )


@dataclass
class PCBLayoutDocument:
    """The routable copper layer of a board: traces, vias, and design rules.

    Component placement stays in the PCBComponent DB rows (already
    normalized there); this only covers what doesn't have its own table.
    """

    design_rules: DesignRules = field(default_factory=DesignRules)
    traces: dict[str, TraceSegment] = field(default_factory=dict)
    vias: dict[str, Via] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "design_rules": self.design_rules.to_dict(),
            "traces": {tid: t.to_dict() for tid, t in self.traces.items()},
            "vias": {vid: v.to_dict() for vid, v in self.vias.items()},
        }

    @staticmethod
    def from_dict(data: dict) -> "PCBLayoutDocument":
        data = data or {}
        return PCBLayoutDocument(
            design_rules=DesignRules.from_dict(data.get("design_rules", {})),
            traces={tid: TraceSegment.from_dict(t) for tid, t in data.get("traces", {}).items()},
            vias={vid: Via.from_dict(v) for vid, v in data.get("vias", {}).items()},
        )


@dataclass
class Net:
    """An electrical net, derived from component pad->net assignments
    (PCBComponent.data["net_map"]) rather than kept as a separate registry —
    there's nothing to fall out of sync with that way."""

    name: str
    pins: list[tuple[str, str]] = field(default_factory=list)  # (reference_designator, pad_id)
    net_class: str = "default"

    def to_dict(self) -> dict:
        return {"name": self.name, "pins": [list(p) for p in self.pins], "class": self.net_class}


def build_nets(components: list) -> dict[str, Net]:
    """Derive nets from every component's pad->net map.

    `components` are PCBComponent ORM rows; each may carry
    `data["net_map"] = {pad_id: net_name}`.
    """
    nets: dict[str, Net] = {}
    for component in components:
        net_map = (component.data or {}).get("net_map", {})
        for pad_id, net_name in net_map.items():
            net = nets.setdefault(net_name, Net(net_name))
            net.pins.append((component.reference_designator, pad_id))
    return nets


def rotate_point(x: float, y: float, degrees: float) -> tuple[float, float]:
    rad = math.radians(degrees)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    return x * cos_a - y * sin_a, x * sin_a + y * cos_a


def pad_world_position(component, pad: dict) -> Point:
    """Absolute board-space position of a footprint pad given the
    component's placement (position + rotation)."""
    rx, ry = rotate_point(float(pad.get("x", 0.0)), float(pad.get("y", 0.0)), component.rotation_degrees)
    return Point(component.position_x + rx, component.position_y + ry)


def footprint_pads_by_id(footprint) -> dict[str, dict]:
    """Index a Footprint row's `pads` list by pad id for O(1) lookup."""
    if not footprint:
        return {}
    return {str(pad.get("id", pad.get("name"))): pad for pad in footprint.pads}


def footprint_keepout_radius(footprint) -> float:
    """Rough keep-clear radius around a component's origin, from its
    courtyard outline if defined, else its pad extent, else a safe
    default. Shared by the router (obstacle marking) and DRC (component
    overlap) so both agree on how big a placed part is."""
    points: list[dict] = []
    if footprint:
        points.extend(footprint.courtyard or [])
        points.extend({"x": pad.get("x", 0), "y": pad.get("y", 0)} for pad in footprint.pads)
    if not points:
        return 2.0
    return max(2.0, max(math.hypot(p.get("x", 0), p.get("y", 0)) for p in points))
