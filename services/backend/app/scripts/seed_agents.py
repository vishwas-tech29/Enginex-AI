"""Seed the AI agent roster described in docs/architecture/ai-agents.md.

Run with: python -m app.scripts.seed_agents
Idempotent — skips agents whose name already exists.
"""
from app.database import SessionLocal
from app.models.ai_chat import AIAgent

AGENTS = [
    {"name": "PlannerAgent", "role": "planning", "prompt": "Break high-level requests into work items."},
    {"name": "MechanicalCADAgent", "role": "cad", "prompt": "Create parametric features and geometry operations."},
    {"name": "PCBDesignAgent", "role": "pcb", "prompt": "Suggest layouts and routing heuristics."},
    {"name": "ElectronicsAgent", "role": "electronics", "prompt": "Evaluate circuits and component compatibility."},
    {"name": "SimulationAgent", "role": "simulation", "prompt": "Execute FEA, SPICE, or motion analysis jobs."},
    {"name": "FirmwareAgent", "role": "firmware", "prompt": "Write embedded C/C++ or Rust code."},
    {"name": "ManufacturingAgent", "role": "manufacturing", "prompt": "Estimate BOM cost and assembly feasibility."},
    {"name": "DesignReviewAgent", "role": "review", "prompt": "Perform QA, DRC, and release checks."},
    {"name": "DocumentationAgent", "role": "documentation", "prompt": "Create design notes, user guides, and handoffs."},
]


def seed() -> None:
    db = SessionLocal()
    try:
        created = 0
        for agent in AGENTS:
            if db.query(AIAgent).filter(AIAgent.name == agent["name"]).first():
                continue
            db.add(AIAgent(**agent, tools=[], memory_enabled=True))
            created += 1
        db.commit()
        print(f"Seeded {created} new agents.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
