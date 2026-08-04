"""Manual + auto trace routing.

Auto-routing is deliberately a "simplified A* pathfinding on grid" (per the
PCB roadmap deliverable) rather than a full topological/rip-up-and-retry
router — it's good enough to connect two-pin nets on an empty-ish board and
gives the AI agent path something real to call, not a production
autorouter replacement for a human (or KiCad's freerouting) on a dense board.
"""

import heapq
import math
import uuid

from app.pcb.layers import LayerType
from app.pcb.layout import (
    Point,
    TraceSegment,
    Via,
    PCBLayoutDocument,
    build_nets,
    footprint_keepout_radius,
    footprint_pads_by_id,
    pad_world_position,
)

DEFAULT_GRID_SIZE_MM = 0.25


class RoutingGrid:
    """Sparse occupancy grid for pathfinding — only occupied cells are
    stored, so a 300mm x 300mm board doesn't preallocate millions of
    always-empty cell objects up front."""

    def __init__(self, width_mm: float, height_mm: float, grid_size_mm: float = DEFAULT_GRID_SIZE_MM):
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.grid_size = grid_size_mm
        self.width_cells = max(1, int(width_mm / grid_size_mm))
        self.height_cells = max(1, int(height_mm / grid_size_mm))
        self.obstacles: set[tuple[int, int]] = set()

    def mm_to_grid(self, mm: float) -> int:
        return int(round(mm / self.grid_size))

    def grid_to_mm(self, cell: int) -> float:
        return cell * self.grid_size

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width_cells and 0 <= y < self.height_cells

    def is_occupied(self, x: int, y: int) -> bool:
        return (x, y) in self.obstacles

    def mark_obstacle(self, x_mm: float, y_mm: float, radius_mm: float) -> None:
        cx, cy = self.mm_to_grid(x_mm), self.mm_to_grid(y_mm)
        radius_cells = max(1, self.mm_to_grid(radius_mm))
        for x in range(cx - radius_cells, cx + radius_cells + 1):
            for y in range(cy - radius_cells, cy + radius_cells + 1):
                if self.in_bounds(x, y) and (x - cx) ** 2 + (y - cy) ** 2 <= radius_cells**2:
                    self.obstacles.add((x, y))

    def clear_obstacle(self, x_mm: float, y_mm: float, radius_mm: float) -> None:
        cx, cy = self.mm_to_grid(x_mm), self.mm_to_grid(y_mm)
        radius_cells = max(1, self.mm_to_grid(radius_mm))
        for x in range(cx - radius_cells, cx + radius_cells + 1):
            for y in range(cy - radius_cells, cy + radius_cells + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= radius_cells**2:
                    self.obstacles.discard((x, y))


def astar_pathfind(grid: RoutingGrid, start: Point, end: Point, max_iterations: int = 20000) -> list[Point] | None:
    """4-directional A* on the grid. The destination cell is always
    reachable even if marked occupied (it's usually the target pad, which
    obstacle-marking treats like any other pad)."""
    start_cell = (grid.mm_to_grid(start.x), grid.mm_to_grid(start.y))
    end_cell = (grid.mm_to_grid(end.x), grid.mm_to_grid(end.y))

    if start_cell == end_cell:
        return [start, end]

    def heuristic(cell: tuple[int, int]) -> int:
        return abs(cell[0] - end_cell[0]) + abs(cell[1] - end_cell[1])

    open_heap: list[tuple[int, tuple[int, int]]] = [(heuristic(start_cell), start_cell)]
    g_cost = {start_cell: 0}
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    closed: set[tuple[int, int]] = set()

    iterations = 0
    while open_heap and iterations < max_iterations:
        iterations += 1
        _, current = heapq.heappop(open_heap)
        if current in closed:
            continue
        if current == end_cell:
            cells = [current]
            while current in came_from:
                current = came_from[current]
                cells.append(current)
            cells.reverse()
            path = [Point(grid.grid_to_mm(x), grid.grid_to_mm(y)) for x, y in cells]
            path[0] = start
            path[-1] = end
            return path

        closed.add(current)
        for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            neighbor = (current[0] + dx, current[1] + dy)
            if neighbor in closed or not grid.in_bounds(*neighbor):
                continue
            if neighbor != end_cell and grid.is_occupied(*neighbor):
                continue
            tentative = g_cost[current] + 1
            if tentative < g_cost.get(neighbor, math.inf):
                g_cost[neighbor] = tentative
                came_from[neighbor] = current
                heapq.heappush(open_heap, (tentative + heuristic(neighbor), neighbor))

    return None


def add_manual_trace(
    doc: PCBLayoutDocument,
    segment_id: str,
    start: Point,
    end: Point,
    layer: LayerType,
    net: str,
    width: float | None = None,
) -> TraceSegment:
    trace = TraceSegment(segment_id, layer, start, end, width or doc.design_rules.min_trace_width, net)
    doc.traces[segment_id] = trace
    return trace


def add_via(
    doc: PCBLayoutDocument,
    via_id: str,
    position: Point,
    from_layer: LayerType,
    to_layer: LayerType,
    net: str,
    pad_diameter: float | None = None,
    drill_diameter: float | None = None,
) -> Via:
    via = Via(
        via_id,
        position,
        pad_diameter or doc.design_rules.min_via_pad_dia,
        drill_diameter or doc.design_rules.min_via_drill_dia,
        from_layer,
        to_layer,
        net,
    )
    doc.vias[via_id] = via
    return via


def auto_route_board(
    doc: PCBLayoutDocument,
    board_width: float,
    board_height: float,
    components: list,
    footprints_by_id: dict[str, object],
    layer: LayerType = LayerType.TOP_COPPER,
    grid_size_mm: float = DEFAULT_GRID_SIZE_MM,
) -> list[TraceSegment]:
    """Route every net that isn't already fully connected, using consecutive
    pin-to-pin A* paths. Already-placed components are obstacles; each
    routed segment becomes an obstacle for nets routed after it, so later
    nets don't overlap earlier ones."""
    nets = build_nets(components)
    components_by_ref = {c.reference_designator: c for c in components}
    grid = RoutingGrid(board_width, board_height, grid_size_mm)

    # (x, y, radius) per component, so a pin-pair route can temporarily lift
    # its own two endpoint components' keep-outs — a courtyard/keep-out
    # circle routinely covers its own pads (that's the point of a
    # courtyard), so leaving it in place while routing FROM one of those
    # pads would seal the pin inside its own obstacle with no way out.
    # Other components stay blocking throughout.
    keepouts: dict[str, tuple[float, float, float]] = {}
    for component in components:
        footprint = footprints_by_id.get(str(component.footprint_id)) if component.footprint_id else None
        radius = footprint_keepout_radius(footprint)
        keepouts[component.reference_designator] = (component.position_x, component.position_y, radius)
        grid.mark_obstacle(component.position_x, component.position_y, radius)

    new_traces: list[TraceSegment] = []
    for net_name, net in nets.items():
        pin_positions: list[Point] = []
        pin_owners: list[str] = []
        for ref, pad_id in net.pins:
            component = components_by_ref.get(ref)
            if not component:
                continue
            footprint = footprints_by_id.get(str(component.footprint_id)) if component.footprint_id else None
            pad = footprint_pads_by_id(footprint).get(pad_id)
            if pad is None:
                continue
            pin_positions.append(pad_world_position(component, pad))
            pin_owners.append(ref)

        for i in range(len(pin_positions) - 1):
            endpoints = {pin_owners[i], pin_owners[i + 1]}
            for ref in endpoints:
                x, y, r = keepouts[ref]
                grid.clear_obstacle(x, y, r)

            path = astar_pathfind(grid, pin_positions[i], pin_positions[i + 1])

            for ref in endpoints:
                x, y, r = keepouts[ref]
                grid.mark_obstacle(x, y, r)

            if not path:
                continue
            for j in range(len(path) - 1):
                segment_id = f"auto_{net_name}_{i}_{j}_{uuid.uuid4().hex[:6]}"
                trace = add_manual_trace(doc, segment_id, path[j], path[j + 1], layer, net_name)
                new_traces.append(trace)
                grid.mark_obstacle(path[j].x, path[j].y, doc.design_rules.min_clearance)
            grid.mark_obstacle(path[-1].x, path[-1].y, doc.design_rules.min_clearance)

    return new_traces


def _collinear_overlapping(t1: TraceSegment, t2: TraceSegment) -> bool:
    if t1.layer != t2.layer or t1.net != t2.net:
        return False
    t1_horizontal = abs(t1.start.y - t1.end.y) < 1e-6
    t2_horizontal = abs(t2.start.y - t2.end.y) < 1e-6
    if t1_horizontal and t2_horizontal:
        return abs(t1.start.y - t2.start.y) < 1e-6
    t1_vertical = abs(t1.start.x - t1.end.x) < 1e-6
    t2_vertical = abs(t2.start.x - t2.end.x) < 1e-6
    if t1_vertical and t2_vertical:
        return abs(t1.start.x - t2.start.x) < 1e-6
    return False


def optimize_traces(doc: PCBLayoutDocument, net: str) -> int:
    """Drop zero-length segments and the shorter of any two collinear,
    same-layer segments on the net. Returns the number removed."""
    ids = [tid for tid, t in doc.traces.items() if t.net == net]
    removed = 0

    for tid in list(ids):
        trace = doc.traces.get(tid)
        if trace is not None and trace.length() < 1e-9:
            del doc.traces[tid]
            ids.remove(tid)
            removed += 1

    for i, id1 in enumerate(ids):
        t1 = doc.traces.get(id1)
        if t1 is None:
            continue
        for id2 in ids[i + 1 :]:
            t2 = doc.traces.get(id2)
            if t2 is None:
                continue
            if _collinear_overlapping(t1, t2):
                shorter_id = id1 if t1.length() <= t2.length() else id2
                if shorter_id in doc.traces:
                    del doc.traces[shorter_id]
                    removed += 1

    return removed
