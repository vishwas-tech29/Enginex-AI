from app.ai.tools import cad_tools, component_tools, pcb_tools, project_tools, simulation_tools
from app.ai.tools.registry import ToolRegistry, tool_registry

_initialized = False


def ensure_tools_registered() -> ToolRegistry:
    """Idempotently populate the global tool registry. Safe to call repeatedly."""
    global _initialized
    if not _initialized:
        cad_tools.register()
        pcb_tools.register()
        component_tools.register()
        simulation_tools.register()
        project_tools.register()
        _initialized = True
    return tool_registry
