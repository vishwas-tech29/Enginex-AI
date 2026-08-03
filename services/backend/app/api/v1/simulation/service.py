import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.projects.service import ROLE_EDITOR, ROLE_VIEWER, ProjectService
from app.api.v1.simulation.schemas import CreateSimulationJobRequest
from app.core.exceptions import ConflictError, NotFoundError
from app.models.project import Project
from app.models.simulation import SimulationJob

TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


class SimulationService:
    """Job lifecycle/state-machine for simulation runs.

    No engine executes these yet (FEA/SPICE/motion analysis is Phase 4 per
    docs/architecture/roadmap.md) — jobs persist in "queued" until a worker
    picks them up. This lays down the API contract and permission checks
    that engine will plug into.
    """

    def __init__(self, db: Session):
        self.db = db
        self.projects = ProjectService(db)

    def _project_for(self, project_id: uuid.UUID, user, min_role: str) -> Project:
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        self.projects.require_access(project, user, min_role)
        return project

    def create(self, payload: CreateSimulationJobRequest, user) -> SimulationJob:
        self._project_for(payload.project_id, user, ROLE_EDITOR)
        job = SimulationJob(
            project_id=payload.project_id,
            file_id=payload.file_id,
            job_type=payload.job_type,
            parameters=payload.parameters,
            status="queued",
            created_by=user.id,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get(self, job_id: uuid.UUID, user) -> SimulationJob:
        job = self.db.get(SimulationJob, job_id)
        if not job:
            raise NotFoundError("Simulation job", job_id)
        self._project_for(job.project_id, user, ROLE_VIEWER)
        return job

    def cancel(self, job_id: uuid.UUID, user) -> SimulationJob:
        job = self.get(job_id, user)
        if job.status in TERMINAL_STATUSES:
            raise ConflictError(f"Job already {job.status}, cannot cancel")
        job.status = "cancelled"
        job.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_results(self, job_id: uuid.UUID, user) -> dict:
        job = self.get(job_id, user)
        if job.status != "completed":
            raise ConflictError(f"Job is {job.status}, no results available yet")
        return job.result or {}

    def get_report_url(self, job_id: uuid.UUID, user) -> str:
        job = self.get(job_id, user)
        if not job.report_url:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No report available for this job")
        return job.report_url
