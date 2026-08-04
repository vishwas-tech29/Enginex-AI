import math
from dataclasses import dataclass

from app.pcb.geometry import point_to_segment_distance, segment_to_segment_distance
from app.pcb.layout import PCBLayoutDocument, TraceSegment, footprint_keepout_radius, footprint_pads_by_id, pad_world_position


@dataclass
class DRCViolation:
    violation_id: str
    rule: str
    severity: str  # "error" | "warning"
    location: tuple[float, float]
    affected_items: list[str]
    message: str

    def to_dict(self) -> dict:
        return {
            "id": self.violation_id,
            "rule": self.rule,
            "severity": self.severity,
            "location": list(self.location),
            "items": self.affected_items,
            "message": self.message,
        }


def run_drc(doc: PCBLayoutDocument, components: list, footprints_by_id: dict[str, object]) -> list[DRCViolation]:
    violations: list[DRCViolation] = []
    violations += _check_trace_width(doc)
    violations += _check_trace_clearance(doc)
    violations += _check_via_sizes(doc)
    violations += _check_trace_pad_spacing(doc, components, footprints_by_id)
    violations += _check_acute_angles(doc)
    violations += _check_component_overlap(components, footprints_by_id)
    return violations


def _check_trace_width(doc: PCBLayoutDocument) -> list[DRCViolation]:
    violations = []
    for trace in doc.traces.values():
        if trace.width < doc.design_rules.min_trace_width:
            violations.append(
                DRCViolation(
                    f"width_{trace.segment_id}",
                    "min_trace_width",
                    "error",
                    (trace.start.x, trace.start.y),
                    [trace.segment_id],
                    f"Trace width {trace.width}mm is below minimum {doc.design_rules.min_trace_width}mm",
                )
            )
    return violations


def _check_trace_clearance(doc: PCBLayoutDocument) -> list[DRCViolation]:
    violations = []
    traces = list(doc.traces.values())
    for i, t1 in enumerate(traces):
        for t2 in traces[i + 1 :]:
            if t1.net == t2.net or t1.layer != t2.layer:
                continue
            distance = segment_to_segment_distance(t1.start, t1.end, t2.start, t2.end)
            required = doc.design_rules.min_clearance + t1.width / 2 + t2.width / 2
            if distance < required:
                violations.append(
                    DRCViolation(
                        f"clearance_{t1.segment_id}_{t2.segment_id}",
                        "trace_clearance",
                        "error",
                        (t1.start.x, t1.start.y),
                        [t1.segment_id, t2.segment_id],
                        f"Clearance {distance:.3f}mm between nets '{t1.net}' and '{t2.net}' is below minimum {required:.3f}mm",
                    )
                )
    return violations


def _check_via_sizes(doc: PCBLayoutDocument) -> list[DRCViolation]:
    violations = []
    for via in doc.vias.values():
        if via.pad_diameter < doc.design_rules.min_via_pad_dia:
            violations.append(
                DRCViolation(
                    f"via_pad_{via.via_id}",
                    "min_via_pad_diameter",
                    "error",
                    (via.position.x, via.position.y),
                    [via.via_id],
                    f"Via pad diameter {via.pad_diameter}mm is below minimum {doc.design_rules.min_via_pad_dia}mm",
                )
            )
        if via.drill_diameter < doc.design_rules.min_via_drill_dia:
            violations.append(
                DRCViolation(
                    f"via_drill_{via.via_id}",
                    "min_via_drill_diameter",
                    "error",
                    (via.position.x, via.position.y),
                    [via.via_id],
                    f"Via drill diameter {via.drill_diameter}mm is below minimum {doc.design_rules.min_via_drill_dia}mm",
                )
            )
    return violations


def _check_trace_pad_spacing(
    doc: PCBLayoutDocument, components: list, footprints_by_id: dict[str, object]
) -> list[DRCViolation]:
    violations = []
    for trace in doc.traces.values():
        for component in components:
            footprint = footprints_by_id.get(str(component.footprint_id)) if component.footprint_id else None
            if not footprint:
                continue
            for pad_id, pad in footprint_pads_by_id(footprint).items():
                pad_net = (component.data or {}).get("net_map", {}).get(pad_id)
                if pad_net == trace.net:
                    continue  # same net, no spacing required
                pad_point = pad_world_position(component, pad)
                distance = point_to_segment_distance(pad_point, trace.start, trace.end)
                pad_radius = max(pad.get("width", 0.5), pad.get("height", 0.5)) / 2
                required = doc.design_rules.min_clearance + trace.width / 2 + pad_radius
                if distance < required:
                    violations.append(
                        DRCViolation(
                            f"pad_trace_{component.reference_designator}_{pad_id}_{trace.segment_id}",
                            "trace_pad_spacing",
                            "error",
                            (trace.start.x, trace.start.y),
                            [str(component.id), trace.segment_id],
                            f"Pad {component.reference_designator}:{pad_id} is {distance:.3f}mm from trace "
                            f"'{trace.net}', below minimum {required:.3f}mm",
                        )
                    )
    return violations


def _trace_angle_degrees(t1: TraceSegment, t2: TraceSegment, shared: tuple[float, float]) -> float:
    def vector_from(trace: TraceSegment) -> tuple[float, float]:
        far = trace.end if (trace.start.x, trace.start.y) == shared else trace.start
        return far.x - shared[0], far.y - shared[1]

    v1, v2 = vector_from(t1), vector_from(t2)
    len1, len2 = math.hypot(*v1), math.hypot(*v2)
    if len1 < 1e-9 or len2 < 1e-9:
        return 180.0
    cos_angle = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (len1 * len2)))
    return math.degrees(math.acos(cos_angle))


def _check_acute_angles(doc: PCBLayoutDocument) -> list[DRCViolation]:
    """Flag sharp bends where two same-net traces meet — acute copper
    angles trap etchant and are a fab-yield red flag, not just cosmetic."""
    violations = []
    by_endpoint: dict[tuple[float, float], list[TraceSegment]] = {}
    for trace in doc.traces.values():
        for endpoint in ((trace.start.x, trace.start.y), (trace.end.x, trace.end.y)):
            by_endpoint.setdefault(endpoint, []).append(trace)

    seen_pairs: set[tuple[str, str]] = set()
    for endpoint, traces_here in by_endpoint.items():
        if len(traces_here) < 2:
            continue
        for i, t1 in enumerate(traces_here):
            for t2 in traces_here[i + 1 :]:
                if t1.net != t2.net or t1.segment_id == t2.segment_id:
                    continue
                pair = tuple(sorted((t1.segment_id, t2.segment_id)))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                angle = _trace_angle_degrees(t1, t2, endpoint)
                if angle < 90:
                    violations.append(
                        DRCViolation(
                            f"angle_{t1.segment_id}_{t2.segment_id}",
                            "acute_angle",
                            "warning",
                            endpoint,
                            [t1.segment_id, t2.segment_id],
                            f"Traces on net '{t1.net}' meet at {angle:.0f}°, below the 90° minimum bend angle",
                        )
                    )
    return violations


def _check_component_overlap(components: list, footprints_by_id: dict[str, object]) -> list[DRCViolation]:
    violations = []
    for i, c1 in enumerate(components):
        for c2 in components[i + 1 :]:
            side1 = (c1.data or {}).get("side", "top")
            side2 = (c2.data or {}).get("side", "top")
            if side1 != side2:
                continue
            fp1 = footprints_by_id.get(str(c1.footprint_id)) if c1.footprint_id else None
            fp2 = footprints_by_id.get(str(c2.footprint_id)) if c2.footprint_id else None
            distance = math.hypot(c1.position_x - c2.position_x, c1.position_y - c2.position_y)
            required = footprint_keepout_radius(fp1) + footprint_keepout_radius(fp2)
            if distance < required:
                violations.append(
                    DRCViolation(
                        f"overlap_{c1.reference_designator}_{c2.reference_designator}",
                        "component_overlap",
                        "warning",
                        (c1.position_x, c1.position_y),
                        [str(c1.id), str(c2.id)],
                        f"Components {c1.reference_designator} and {c2.reference_designator} are "
                        f"{distance:.2f}mm apart, closer than their combined keep-out of {required:.2f}mm",
                    )
                )
    return violations
