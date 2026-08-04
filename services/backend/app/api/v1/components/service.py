import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.v1.components.schemas import CreateFootprintRequest, CreateSymbolRequest
from app.core.exceptions import NotFoundError
from app.models.component import Component, Footprint, Symbol


class ComponentService:
    def __init__(self, db: Session):
        self.db = db

    def search(self, q: str, category: str | None, limit: int) -> list[Component]:
        query = self.db.query(Component)
        if category:
            query = query.filter(Component.category == category)
        like = f"%{q}%"
        query = query.filter(
            or_(
                Component.name.ilike(like),
                Component.part_number.ilike(like),
                Component.manufacturer.ilike(like),
            )
        )
        return query.limit(limit).all()

    def list_all(self, category: str | None, limit: int, skip: int) -> list[Component]:
        query = self.db.query(Component)
        if category:
            query = query.filter(Component.category == category)
        return query.offset(skip).limit(limit).all()

    def get(self, component_id: uuid.UUID) -> Component:
        component = self.db.get(Component, component_id)
        if not component:
            raise NotFoundError("Component", component_id)
        return component

    def get_datasheet_redirect(self, component_id: uuid.UUID) -> RedirectResponse:
        component = self.get(component_id)
        if not component.datasheet_url:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No datasheet on file for this component")
        return RedirectResponse(url=component.datasheet_url)

    def list_symbols(self, library: str | None) -> list[Symbol]:
        query = self.db.query(Symbol)
        if library:
            query = query.filter(Symbol.library == library)
        return query.all()

    def create_symbol(self, payload: CreateSymbolRequest) -> Symbol:
        symbol = Symbol(
            name=payload.name,
            library=payload.library,
            svg_data=payload.svg_data,
            pins=payload.pins,
            meta=payload.meta,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(symbol)
        self.db.commit()
        self.db.refresh(symbol)
        return symbol

    def get_footprints_by_ids(self, footprint_ids: list[uuid.UUID]) -> dict[str, Footprint]:
        """Bulk lookup keyed by string id, for engines that need to resolve
        many components' footprints without an N+1 query per component."""
        ids = {fid for fid in footprint_ids if fid is not None}
        if not ids:
            return {}
        rows = self.db.query(Footprint).filter(Footprint.id.in_(ids)).all()
        return {str(row.id): row for row in rows}

    def get_components_by_ids(self, component_ids: list[uuid.UUID]) -> dict[str, Component]:
        """Bulk lookup of shared library Components (category/part number/
        manufacturer), keyed by string id — mirrors get_footprints_by_ids."""
        ids = {cid for cid in component_ids if cid is not None}
        if not ids:
            return {}
        rows = self.db.query(Component).filter(Component.id.in_(ids)).all()
        return {str(row.id): row for row in rows}

    def list_footprints(self, package_type: str | None) -> list[Footprint]:
        query = self.db.query(Footprint)
        if package_type:
            query = query.filter(Footprint.package_type == package_type)
        return query.all()

    def create_footprint(self, payload: CreateFootprintRequest) -> Footprint:
        footprint = Footprint(
            name=payload.name,
            package_type=payload.package_type,
            pads=payload.pads,
            courtyard=payload.courtyard,
            silkscreen=payload.silkscreen,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(footprint)
        self.db.commit()
        self.db.refresh(footprint)
        return footprint
