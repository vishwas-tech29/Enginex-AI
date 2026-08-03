import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import UUIDPKMixin


class Symbol(Base, UUIDPKMixin):
    __tablename__ = "symbols"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    library: Mapped[str] = mapped_column(String(100), nullable=False, default="Enginex Standard")
    svg_data: Mapped[str] = mapped_column(Text, nullable=False, default="")
    pins: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    meta: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class Footprint(Base, UUIDPKMixin):
    __tablename__ = "footprints"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    package_type: Mapped[str] = mapped_column(String(100), nullable=False)
    pads: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    courtyard: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    silkscreen: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class Component(Base, UUIDPKMixin):
    __tablename__ = "components"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    part_number: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    datasheet_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    symbol_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("symbols.id", ondelete="SET NULL"), nullable=True
    )
    footprint_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("footprints.id", ondelete="SET NULL"), nullable=True
    )
    meta: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
