import uuid

from app.ai.tools.context import ToolContext
from app.ai.tools.registry import tool_registry
from app.api.v1.pcb.schemas import (
    AddTraceRequest,
    AutoRouteRequest,
    CreateBoardRequest,
    CreateComponentRequest,
    UpdateComponentRequest,
    XYPoint,
)
from app.api.v1.pcb.service import PCBService

ROLES = ["pcb_designer", "design_review"]


async def create_pcb_board(ctx: ToolContext, file_id: str, name: str, width_mm: float, height_mm: float) -> dict:
    """Create a new PCB board outline on a file."""
    board = PCBService(ctx.db).create_board(
        CreateBoardRequest(file_id=uuid.UUID(file_id), name=name, width_mm=width_mm, height_mm=height_mm),
        ctx.user,
    )
    return {"board_id": str(board.id), "name": board.name}


async def get_pcb_board(ctx: ToolContext, board_id: str) -> dict:
    """Fetch a PCB board's current state."""
    board = PCBService(ctx.db).get_board(uuid.UUID(board_id), ctx.user)
    return {"board_id": str(board.id), "name": board.name, "layers_count": board.layers_count}


async def place_component(
    ctx: ToolContext, board_id: str, reference_designator: str, position_x: float, position_y: float
) -> dict:
    """Place a component footprint on the board at (x, y) millimeters."""
    component = PCBService(ctx.db).create_component(
        CreateComponentRequest(
            board_id=uuid.UUID(board_id),
            reference_designator=reference_designator,
            position_x=position_x,
            position_y=position_y,
        ),
        ctx.user,
    )
    return {"component_id": str(component.id), "reference_designator": component.reference_designator}


async def move_component(ctx: ToolContext, component_id: str, position_x: float, position_y: float) -> dict:
    """Move an already-placed component to new (x, y) coordinates."""
    component = PCBService(ctx.db).update_component(
        uuid.UUID(component_id),
        UpdateComponentRequest(position_x=position_x, position_y=position_y),
        ctx.user,
    )
    return {"component_id": str(component.id), "position": {"x": component.position_x, "y": component.position_y}}


async def run_design_rule_check(ctx: ToolContext, board_id: str) -> dict:
    """Run a design rule check (DRC) on the board and return any violations."""
    violations = PCBService(ctx.db).run_drc(uuid.UUID(board_id), ctx.user)
    return {"violations": violations}


async def run_electrical_rule_check(ctx: ToolContext, board_id: str) -> dict:
    """Run an electrical rule check (ERC) on the board and return any violations."""
    violations = PCBService(ctx.db).run_erc(uuid.UUID(board_id), ctx.user)
    return {"violations": violations}


async def route_trace(
    ctx: ToolContext,
    board_id: str,
    layer: str,
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    net: str,
    width_mm: float | None = None,
) -> dict:
    """Draw a copper trace between two points on one layer, on a given net."""
    trace = PCBService(ctx.db).add_trace(
        uuid.UUID(board_id),
        AddTraceRequest(
            layer=layer, start=XYPoint(x=start_x, y=start_y), end=XYPoint(x=end_x, y=end_y),
            net=net, width=width_mm,
        ),
        ctx.user,
    )
    return trace


async def auto_route_board(ctx: ToolContext, board_id: str, layer: str = "top_copper") -> dict:
    """Auto-route every net on the board that isn't fully connected yet."""
    traces = PCBService(ctx.db).auto_route(uuid.UUID(board_id), AutoRouteRequest(layer=layer), ctx.user)
    return {"traces": traces}


def register() -> None:
    tool_registry.register("create_pcb_board", create_pcb_board.__doc__, create_pcb_board, ROLES)
    tool_registry.register("get_pcb_board", get_pcb_board.__doc__, get_pcb_board, ROLES)
    tool_registry.register("place_component", place_component.__doc__, place_component, ROLES)
    tool_registry.register("move_component", move_component.__doc__, move_component, ROLES)
    tool_registry.register(
        "run_design_rule_check", run_design_rule_check.__doc__, run_design_rule_check, ROLES
    )
    tool_registry.register(
        "run_electrical_rule_check", run_electrical_rule_check.__doc__, run_electrical_rule_check, ROLES
    )
    tool_registry.register("route_trace", route_trace.__doc__, route_trace, ROLES)
    tool_registry.register("auto_route_board", auto_route_board.__doc__, auto_route_board, ROLES)
