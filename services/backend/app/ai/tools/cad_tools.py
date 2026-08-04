import uuid

from app.ai.tools.context import ToolContext
from app.ai.tools.registry import tool_registry
from app.api.v1.cad.schemas import (
    AddCircleRequest,
    AddLineRequest,
    AddPointRequest,
    CreateBodyRequest,
    CreateSketchRequest,
    ExtrudeRequest,
    FilletRequest,
    ChamferRequest,
    RevolveRequest,
)
from app.api.v1.cad.service import CADService

ROLES = ["mechanical_engineer", "design_review"]


async def create_sketch(ctx: ToolContext, file_id: str, name: str) -> dict:
    """Create a new, empty sketch on a CAD file."""
    sketch = CADService(ctx.db).create_sketch(
        CreateSketchRequest(file_id=uuid.UUID(file_id), name=name), ctx.user
    )
    return {"sketch_id": str(sketch.id), "name": sketch.name}


async def get_sketch(ctx: ToolContext, sketch_id: str) -> dict:
    """Fetch a sketch's current points/lines/circles/arcs/constraints."""
    sketch = CADService(ctx.db).get(uuid.UUID(sketch_id), ctx.user)
    return {"sketch_id": str(sketch.id), "name": sketch.name, "data": sketch.data}


async def add_sketch_point(ctx: ToolContext, sketch_id: str, x: float, y: float) -> dict:
    """Add a 2D point to a sketch. Returns the new point's ID for use in add_sketch_line/circle."""
    return CADService(ctx.db).add_point(uuid.UUID(sketch_id), AddPointRequest(x=x, y=y), ctx.user)


async def add_sketch_line(ctx: ToolContext, sketch_id: str, start_point_id: str, end_point_id: str) -> dict:
    """Add a straight line between two existing points in a sketch."""
    return CADService(ctx.db).add_line(
        uuid.UUID(sketch_id), AddLineRequest(start_id=start_point_id, end_id=end_point_id), ctx.user
    )


async def add_sketch_circle(ctx: ToolContext, sketch_id: str, center_point_id: str, radius_mm: float) -> dict:
    """Add a circle to a sketch, centered on an existing point."""
    return CADService(ctx.db).add_circle(
        uuid.UUID(sketch_id), AddCircleRequest(center_id=center_point_id, radius=radius_mm), ctx.user
    )


async def solve_sketch(ctx: ToolContext, sketch_id: str) -> dict:
    """Solve a sketch's constraints and report whether it's fully constrained."""
    return CADService(ctx.db).solve_sketch(uuid.UUID(sketch_id), ctx.user)


async def list_cad_bodies(ctx: ToolContext, file_id: str) -> dict:
    """List solid bodies already created in a CAD file."""
    bodies = CADService(ctx.db).list_bodies(uuid.UUID(file_id), ctx.user)
    return {"bodies": [{"id": str(b.id), "name": b.name} for b in bodies]}


async def create_body(ctx: ToolContext, file_id: str, name: str) -> dict:
    """Create a new, empty solid body to build features onto (extrude/revolve target)."""
    body = CADService(ctx.db).create_body(CreateBodyRequest(file_id=uuid.UUID(file_id), name=name), ctx.user)
    return {"body_id": str(body.id), "name": body.name}


async def extrude_sketch(ctx: ToolContext, body_id: str, sketch_id: str, distance_mm: float) -> dict:
    """Extrude a closed sketch profile into a 3D solid, adding it to `body_id`."""
    body = CADService(ctx.db).extrude(
        uuid.UUID(body_id), ExtrudeRequest(sketch_id=uuid.UUID(sketch_id), distance=distance_mm), ctx.user
    )
    return {"body_id": str(body.id), "version": body.version_number, "feature_count": len(body.data["features"])}


async def revolve_sketch(ctx: ToolContext, body_id: str, sketch_id: str, angle_degrees: float = 360) -> dict:
    """Revolve a closed sketch profile around the Y axis to create a solid, adding it to `body_id`."""
    body = CADService(ctx.db).revolve(
        uuid.UUID(body_id), RevolveRequest(sketch_id=uuid.UUID(sketch_id), angle=angle_degrees), ctx.user
    )
    return {"body_id": str(body.id), "version": body.version_number}


async def fillet_edges(ctx: ToolContext, body_id: str, radius_mm: float) -> dict:
    """Round every edge of a body with the given fillet radius."""
    body = CADService(ctx.db).fillet(uuid.UUID(body_id), FilletRequest(radius=radius_mm), ctx.user)
    return {"body_id": str(body.id), "version": body.version_number}


async def chamfer_edges(ctx: ToolContext, body_id: str, distance_mm: float) -> dict:
    """Bevel every edge of a body with the given chamfer distance."""
    body = CADService(ctx.db).chamfer(uuid.UUID(body_id), ChamferRequest(distance=distance_mm), ctx.user)
    return {"body_id": str(body.id), "version": body.version_number}


async def get_body_info(ctx: ToolContext, body_id: str) -> dict:
    """Get a body's computed volume, surface area, and bounding box."""
    mesh = CADService(ctx.db).get_mesh(uuid.UUID(body_id), ctx.user)
    return {
        "volume_mm3": mesh["volume"],
        "surface_area_mm2": mesh["surface_area"],
        "bounding_box": mesh["bounding_box"],
    }


def register() -> None:
    tool_registry.register("create_sketch", create_sketch.__doc__, create_sketch, ROLES)
    tool_registry.register("get_sketch", get_sketch.__doc__, get_sketch, ROLES)
    tool_registry.register("add_sketch_point", add_sketch_point.__doc__, add_sketch_point, ROLES)
    tool_registry.register("add_sketch_line", add_sketch_line.__doc__, add_sketch_line, ROLES)
    tool_registry.register("add_sketch_circle", add_sketch_circle.__doc__, add_sketch_circle, ROLES)
    tool_registry.register("solve_sketch", solve_sketch.__doc__, solve_sketch, ROLES)
    tool_registry.register("list_cad_bodies", list_cad_bodies.__doc__, list_cad_bodies, ROLES)
    tool_registry.register("create_body", create_body.__doc__, create_body, ROLES)
    tool_registry.register("extrude_sketch", extrude_sketch.__doc__, extrude_sketch, ROLES)
    tool_registry.register("revolve_sketch", revolve_sketch.__doc__, revolve_sketch, ROLES)
    tool_registry.register("fillet_edges", fillet_edges.__doc__, fillet_edges, ROLES)
    tool_registry.register("chamfer_edges", chamfer_edges.__doc__, chamfer_edges, ROLES)
    tool_registry.register("get_body_info", get_body_info.__doc__, get_body_info, ROLES)
