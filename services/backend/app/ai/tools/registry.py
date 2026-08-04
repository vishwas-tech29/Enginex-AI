import inspect
import logging
from typing import Any, Awaitable, Callable, get_type_hints

logger = logging.getLogger("enginex.ai.tools")

_TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


class Tool:
    """A single tool an agent can call, with an auto-derived JSON schema."""

    def __init__(self, name: str, description: str, func: Callable[..., Awaitable[Any]], roles: list[str]):
        self.name = name
        self.description = description
        self.func = func
        self.roles = roles
        self.input_schema = self._build_input_schema(func)

    def _build_input_schema(self, func: Callable) -> dict[str, Any]:
        sig = inspect.signature(func)
        try:
            hints = get_type_hints(func)
        except Exception:  # noqa: BLE001 — fall back to raw annotations if hints can't resolve
            hints = {}

        properties: dict[str, Any] = {}
        required: list[str] = []

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls", "ctx"):
                continue

            param_type = hints.get(param_name, param.annotation)
            properties[param_name] = {
                "type": self._json_type(param_type),
                "description": param_name.replace("_", " "),
            }
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        return {"type": "object", "properties": properties, "required": required}

    def _json_type(self, python_type: Any) -> str:
        origin = getattr(python_type, "__origin__", None)
        if origin is not None:
            # Optional[X] / X | None -> unwrap to X; anything else generic -> object
            args = [a for a in getattr(python_type, "__args__", []) if a is not type(None)]
            if args:
                return self._json_type(args[0])
            return "object"
        return _TYPE_MAP.get(python_type, "string")

    async def execute(self, ctx: Any, **kwargs: Any) -> Any:
        return await self.func(ctx, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "input_schema": self.input_schema}


class ToolRegistry:
    """Central registry for all agent-callable tools, gated by agent role."""

    def __init__(self) -> None:
        self.tools: dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str,
        func: Callable[..., Awaitable[Any]],
        roles: list[str],
    ) -> None:
        self.tools[name] = Tool(name, description, func, roles)
        logger.debug("tool_registered", extra={"tool": name, "roles": roles})

    async def execute_tool(self, tool_name: str, ctx: Any, **kwargs: Any) -> dict[str, Any]:
        tool = self.tools.get(tool_name)
        if tool is None:
            return {"success": False, "tool": tool_name, "error": f"Tool not found: {tool_name}"}

        try:
            result = await tool.execute(ctx, **kwargs)
            return {"success": True, "tool": tool_name, "result": result}
        except Exception as exc:  # noqa: BLE001 — tool failures shouldn't crash the agent loop
            logger.warning("tool_execution_failed", extra={"tool": tool_name, "error": str(exc)})
            return {"success": False, "tool": tool_name, "error": str(exc)}

    def get_tools_for_role(self, role: str) -> list[dict[str, Any]]:
        return [tool.to_dict() for tool in self.tools.values() if role in tool.roles]

    def has_access(self, role: str, tool_name: str) -> bool:
        tool = self.tools.get(tool_name)
        return tool is not None and role in tool.roles


tool_registry = ToolRegistry()
