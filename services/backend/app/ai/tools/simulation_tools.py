import uuid

from app.ai.tools.context import ToolContext
from app.ai.tools.registry import tool_registry
from app.api.v1.simulation.schemas import CreateSimulationJobRequest
from app.api.v1.simulation.service import SimulationService

ROLES = ["simulation", "design_review"]


async def create_simulation_job(ctx: ToolContext, project_id: str, job_type: str, file_id: str = "") -> dict:
    """Submit a simulation job (e.g. 'fea', 'spice', 'thermal', 'motion') for a project."""
    job = SimulationService(ctx.db).create(
        CreateSimulationJobRequest(
            project_id=uuid.UUID(project_id),
            file_id=uuid.UUID(file_id) if file_id else None,
            job_type=job_type,
        ),
        ctx.user,
    )
    return {"job_id": str(job.id), "status": job.status}


async def get_simulation_job_status(ctx: ToolContext, job_id: str) -> dict:
    """Check the status of a previously submitted simulation job."""
    job = SimulationService(ctx.db).get(uuid.UUID(job_id), ctx.user)
    return {"job_id": str(job.id), "status": job.status}


async def cancel_simulation_job(ctx: ToolContext, job_id: str) -> dict:
    """Cancel a queued or running simulation job."""
    job = SimulationService(ctx.db).cancel(uuid.UUID(job_id), ctx.user)
    return {"job_id": str(job.id), "status": job.status}


def register() -> None:
    tool_registry.register(
        "create_simulation_job", create_simulation_job.__doc__, create_simulation_job, ROLES
    )
    tool_registry.register(
        "get_simulation_job_status", get_simulation_job_status.__doc__, get_simulation_job_status, ROLES
    )
    tool_registry.register(
        "cancel_simulation_job", cancel_simulation_job.__doc__, cancel_simulation_job, ROLES
    )
