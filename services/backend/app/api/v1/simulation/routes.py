import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.simulation.schemas import CreateSimulationJobRequest, SimulationJobOut
from app.api.v1.simulation.service import SimulationService
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/simulation", tags=["Simulation"])


@router.post("/jobs", response_model=SimulationJobOut, status_code=201)
def create_job(
    payload: CreateSimulationJobRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return SimulationService(db).create(payload, current_user)


@router.get("/jobs/{job_id}", response_model=SimulationJobOut)
def get_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return SimulationService(db).get(job_id, current_user)


@router.post("/jobs/{job_id}/cancel", response_model=SimulationJobOut)
def cancel_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return SimulationService(db).cancel(job_id, current_user)


@router.get("/jobs/{job_id}/results")
def get_results(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return SimulationService(db).get_results(job_id, current_user)


@router.get("/jobs/{job_id}/report")
def get_report(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    url = SimulationService(db).get_report_url(job_id, current_user)
    return RedirectResponse(url=url)
