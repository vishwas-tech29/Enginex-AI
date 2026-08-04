"""2D geometry helpers shared by the DRC and export engines.

Segment-to-segment distance needs an actual intersection test, not just the
minimum of the four endpoint-to-opposite-segment distances — two segments
can cross at an interior point (an X shape) where every endpoint sits well
clear of the other segment, so that shortcut alone would miss real shorts.
"""

from app.pcb.layout import Point


def _orientation(p: Point, q: Point, r: Point) -> int:
    val = (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)
    if abs(val) < 1e-9:
        return 0
    return 1 if val > 0 else 2


def _on_segment(p: Point, q: Point, r: Point) -> bool:
    return (
        min(p.x, r.x) - 1e-9 <= q.x <= max(p.x, r.x) + 1e-9
        and min(p.y, r.y) - 1e-9 <= q.y <= max(p.y, r.y) + 1e-9
    )


def segments_intersect(a1: Point, a2: Point, b1: Point, b2: Point) -> bool:
    o1, o2 = _orientation(a1, a2, b1), _orientation(a1, a2, b2)
    o3, o4 = _orientation(b1, b2, a1), _orientation(b1, b2, a2)

    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and _on_segment(a1, b1, a2):
        return True
    if o2 == 0 and _on_segment(a1, b2, a2):
        return True
    if o3 == 0 and _on_segment(b1, a1, b2):
        return True
    if o4 == 0 and _on_segment(b1, a2, b2):
        return True
    return False


def point_to_segment_distance(p: Point, a: Point, b: Point) -> float:
    dx, dy = b.x - a.x, b.y - a.y
    length_sq = dx * dx + dy * dy
    if length_sq < 1e-12:
        return p.distance_to(a)
    t = max(0.0, min(1.0, ((p.x - a.x) * dx + (p.y - a.y) * dy) / length_sq))
    return p.distance_to(Point(a.x + t * dx, a.y + t * dy))


def segment_to_segment_distance(a1: Point, a2: Point, b1: Point, b2: Point) -> float:
    if segments_intersect(a1, a2, b1, b2):
        return 0.0
    return min(
        point_to_segment_distance(a1, b1, b2),
        point_to_segment_distance(a2, b1, b2),
        point_to_segment_distance(b1, a1, a2),
        point_to_segment_distance(b2, a1, a2),
    )
