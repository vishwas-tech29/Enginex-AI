import uuid

from app.ai.tools.context import ToolContext
from app.ai.tools.registry import tool_registry
from app.api.v1.components.service import ComponentService

ROLES = ["electronics", "pcb_designer", "manufacturing", "component_recommendation"]


async def search_components(ctx: ToolContext, query: str, category: str = "") -> dict:
    """Search the component library by name, part number, or manufacturer."""
    results = ComponentService(ctx.db).search(query, category or None, limit=10)
    return {
        "components": [
            {"id": str(c.id), "name": c.name, "part_number": c.part_number, "category": c.category}
            for c in results
        ]
    }


async def get_component_details(ctx: ToolContext, component_id: str) -> dict:
    """Get full details for a specific component, including its datasheet URL."""
    component = ComponentService(ctx.db).get(uuid.UUID(component_id))
    return {
        "id": str(component.id),
        "name": component.name,
        "category": component.category,
        "manufacturer": component.manufacturer,
        "part_number": component.part_number,
        "datasheet_url": component.datasheet_url,
    }


def register() -> None:
    tool_registry.register("search_components", search_components.__doc__, search_components, ROLES)
    tool_registry.register(
        "get_component_details", get_component_details.__doc__, get_component_details, ROLES
    )
