import uuid

from app.ai.tools.context import ToolContext
from app.ai.tools.registry import tool_registry
from app.api.v1.cad.schemas import CreateSketchRequest, UpdateSketchRequest
from app.api.v1.cad.service import CADService

ROLES = ["mechanical_engineer", "design_review"]


async def create_sketch(ctx: ToolContext, file_id: str, name: str) -> dict:
    """Create a new sketch on a CAD file."""
    sketch = CADService(ctx.db).create_sketch(
        CreateSketchRequest(file_id=uuid.UUID(file_id), name=name), ctx.user
    )
    return {"sketch_id": str(sketch.id), "name": sketch.name, "version": sketch.version_number}


async def get_sketch(ctx: ToolContext, sketch_id: str) -> dict:
    """Fetch a sketch's current data by ID."""
    sketch = CADService(ctx.db).get(uuid.UUID(sketch_id), ctx.user)
    return {"sketch_id": str(sketch.id), "name": sketch.name, "data": sketch.data}


async def update_sketch_geometry(ctx: ToolContext, sketch_id: str, data: dict) -> dict:
    """Replace a sketch's geometry data (lines, arcs, dimensions)."""
    sketch = CADService(ctx.db).update(
        uuid.UUID(sketch_id), UpdateSketchRequest(data=data), ctx.user
    )
    return {"sketch_id": str(sketch.id), "version": sketch.version_number}


async def list_cad_bodies(ctx: ToolContext, file_id: str) -> dict:
    """List solid bodies already created in a CAD file."""
    bodies = CADService(ctx.db).list_bodies(uuid.UUID(file_id), ctx.user)
    return {"bodies": [{"id": str(b.id), "name": b.name} for b in bodies]}


async def extrude_sketch(ctx: ToolContext, body_id: str, distance_mm: float) -> dict:
    """Extrude a sketch into a 3D solid body by a given distance in mm."""
    CADService(ctx.db).feature_operation(uuid.UUID(body_id), "extrude", ctx.user)
    return {}  # unreachable — feature_operation always raises until Phase 5's geometry kernel lands


async def revolve_sketch(ctx: ToolContext, body_id: str, angle_degrees: float) -> dict:
    """Revolve a sketch around an axis to create a 3D solid body."""
    CADService(ctx.db).feature_operation(uuid.UUID(body_id), "revolve", ctx.user)
    return {}


async def fillet_edges(ctx: ToolContext, body_id: str, radius_mm: float) -> dict:
    """Apply a fillet (rounded edge) to a body."""
    CADService(ctx.db).feature_operation(uuid.UUID(body_id), "fillet", ctx.user)
    return {}


async def chamfer_edges(ctx: ToolContext, body_id: str, distance_mm: float) -> dict:
    """Apply a chamfer (beveled edge) to a body."""
    CADService(ctx.db).feature_operation(uuid.UUID(body_id), "chamfer", ctx.user)
    return {}


def register() -> None:
    tool_registry.register("create_sketch", create_sketch.__doc__, create_sketch, ROLES)
    tool_registry.register("get_sketch", get_sketch.__doc__, get_sketch, ROLES)
    tool_registry.register(
        "update_sketch_geometry", update_sketch_geometry.__doc__, update_sketch_geometry, ROLES
    )
    tool_registry.register("list_cad_bodies", list_cad_bodies.__doc__, list_cad_bodies, ROLES)
    tool_registry.register("extrude_sketch", extrude_sketch.__doc__, extrude_sketch, ROLES)
    tool_registry.register("revolve_sketch", revolve_sketch.__doc__, revolve_sketch, ROLES)
    tool_registry.register("fillet_edges", fillet_edges.__doc__, fillet_edges, ROLES)
    tool_registry.register("chamfer_edges", chamfer_edges.__doc__, chamfer_edges, ROLES)
