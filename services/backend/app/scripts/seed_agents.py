"""Seed the AI agent catalog from app.ai.agents.definitions (the single
source of truth also used to build the runtime LangGraph agents).

Run with: python -m app.scripts.seed_agents
Idempotent — updates role/prompt for agents whose name already exists,
rather than skipping, so the DB catalog can't drift from the code.
"""
from app.ai.agents.definitions import AGENT_DEFINITIONS
from app.ai.tools.registry import ToolRegistry
from app.ai.tools.setup import ensure_tools_registered
from app.database import SessionLocal
from app.models.ai_chat import AIAgent


def seed() -> None:
    registry: ToolRegistry = ensure_tools_registered()
    db = SessionLocal()
    try:
        created, updated = 0, 0
        for definition in AGENT_DEFINITIONS:
            tool_names = [t["name"] for t in registry.get_tools_for_role(definition.role)]
            existing = db.query(AIAgent).filter(AIAgent.name == definition.name).first()
            if existing:
                existing.role = definition.role
                existing.prompt = definition.system_prompt
                existing.tools = tool_names
                updated += 1
            else:
                db.add(
                    AIAgent(
                        name=definition.name,
                        role=definition.role,
                        prompt=definition.system_prompt,
                        tools=tool_names,
                        memory_enabled=True,
                    )
                )
                created += 1
        db.commit()
        print(f"Seeded {created} new agents, updated {updated} existing.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
