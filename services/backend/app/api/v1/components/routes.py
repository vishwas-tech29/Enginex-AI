import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.components.schemas import (
    ComponentOut,
    CreateFootprintRequest,
    CreateSymbolRequest,
    FootprintOut,
    SymbolOut,
)
from app.api.v1.components.service import ComponentService
from app.database import get_db
from app.models.user import User

router = APIRouter(tags=["Components & Libraries"])


@router.get("/components", response_model=list[ComponentOut])
def list_components(
    category: str | None = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ComponentService(db).list_all(category, limit, skip)


@router.get("/components/search", response_model=list[ComponentOut])
def search_components(
    q: str = Query(..., min_length=1),
    category: str | None = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ComponentService(db).search(q, category, limit)


@router.get("/components/{component_id}", response_model=ComponentOut)
def get_component(
    component_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ComponentService(db).get(component_id)


@router.get("/components/{component_id}/datasheet")
def get_datasheet(
    component_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ComponentService(db).get_datasheet_redirect(component_id)


@router.get("/symbols", response_model=list[SymbolOut])
def list_symbols(
    library: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ComponentService(db).list_symbols(library)


@router.post("/symbols", response_model=SymbolOut, status_code=201)
def create_symbol(
    payload: CreateSymbolRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ComponentService(db).create_symbol(payload)


@router.get("/footprints", response_model=list[FootprintOut])
def list_footprints(
    package_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ComponentService(db).list_footprints(package_type)


@router.post("/footprints", response_model=FootprintOut, status_code=201)
def create_footprint(
    payload: CreateFootprintRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ComponentService(db).create_footprint(payload)
