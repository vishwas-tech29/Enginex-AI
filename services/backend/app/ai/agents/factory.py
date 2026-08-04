from app.ai.agents.base_agent import BaseAgent
from app.ai.agents.definitions import AGENT_DEFINITIONS
from app.ai.providers.router import LLMRouter
from app.ai.tools.registry import ToolRegistry


def build_agents(llm_router: LLMRouter, tool_registry: ToolRegistry) -> dict[str, BaseAgent]:
    return {
        definition.key: BaseAgent(
            key=definition.key,
            name=definition.name,
            role=definition.role,
            system_prompt=definition.system_prompt,
            llm_router=llm_router,
            tool_registry=tool_registry,
        )
        for definition in AGENT_DEFINITIONS
    }
