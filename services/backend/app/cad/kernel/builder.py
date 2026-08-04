import math

import cadquery as cq

from app.cad.sketch.entities import SketchDocument

TOLERANCE = 1e-6


class ProfileBuildError(ValueError):
    """The sketch's geometry doesn't form a shape a solid feature can use."""


def _close(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return math.hypot(a[0] - b[0], a[1] - b[1]) < TOLERANCE


def _line_endpoints(doc: SketchDocument, line_id: str) -> tuple[tuple[float, float], tuple[float, float]]:
    line = doc.lines[line_id]
    p1, p2 = doc.points[line.start_id], doc.points[line.end_id]
    return (p1.x, p1.y), (p2.x, p2.y)


def _arc_endpoints(doc: SketchDocument, arc_id: str) -> tuple[tuple[float, float], tuple[float, float]]:
    arc = doc.arcs[arc_id]
    c = doc.points[arc.center_id]
    p1 = (c.x + arc.radius * math.cos(arc.start_angle), c.y + arc.radius * math.sin(arc.start_angle))
    p2 = (c.x + arc.radius * math.cos(arc.end_angle), c.y + arc.radius * math.sin(arc.end_angle))
    return p1, p2


def _arc_midpoint(doc: SketchDocument, arc_id: str) -> tuple[float, float]:
    arc = doc.arcs[arc_id]
    c = doc.points[arc.center_id]
    mid_angle = arc.start_angle + (arc.end_angle - arc.start_angle) / 2
    return (c.x + arc.radius * math.cos(mid_angle), c.y + arc.radius * math.sin(mid_angle))


def build_profile_from_sketch(doc: SketchDocument) -> cq.Workplane:
    """Build a closed, extrudable/revolvable 2D profile from a sketch.

    Supports a single circle, or one closed loop of lines/arcs (endpoints
    matched by coordinate proximity, not shared point IDs — the same
    approach real CAD loop-detection uses, and it means constrained-
    coincident points from separate entities still chain correctly).
    Multiple disjoint loops (holes) and arcs whose sweep crosses 0° aren't
    supported yet — a real scope boundary, not an oversight.
    """
    if not doc.lines and not doc.arcs:
        if len(doc.circles) == 1:
            circle = next(iter(doc.circles.values()))
            center = doc.points[circle.center_id]
            return cq.Workplane("XY").moveTo(center.x, center.y).circle(circle.radius)
        raise ProfileBuildError("Sketch must contain either one circle or a closed loop of lines/arcs")

    edges = [("line", eid) for eid in doc.lines] + [("arc", eid) for eid in doc.arcs]
    remaining = edges[:]
    kind0, id0 = remaining.pop(0)
    endpoints0 = _line_endpoints(doc, id0) if kind0 == "line" else _arc_endpoints(doc, id0)
    start_pt, cur_pt = endpoints0
    chain = [(kind0, id0, start_pt, cur_pt)]

    while remaining:
        match = None
        for kind, eid in remaining:
            p1, p2 = _line_endpoints(doc, eid) if kind == "line" else _arc_endpoints(doc, eid)
            if _close(p1, cur_pt):
                match = (kind, eid, p1, p2)
                break
            if _close(p2, cur_pt):
                match = (kind, eid, p2, p1)
                break
        if match is None:
            raise ProfileBuildError("Sketch geometry doesn't form a single closed loop")
        chain.append(match)
        cur_pt = match[3]
        remaining.remove((match[0], match[1]))

    if not _close(cur_pt, start_pt):
        raise ProfileBuildError("Sketch geometry doesn't form a closed loop")

    wp = cq.Workplane("XY").moveTo(*start_pt)
    for kind, eid, _p_from, p_to in chain:
        if kind == "line":
            wp = wp.lineTo(*p_to)
        else:
            wp = wp.threePointArc(_arc_midpoint(doc, eid), p_to)
    return wp.close()
