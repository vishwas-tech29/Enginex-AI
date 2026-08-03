import uuid

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class PCBBoard(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "pcb_boards"

    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    width_mm: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    height_mm: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    layers_count: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class PCBComponent(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "pcb_components"

    board_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pcb_boards.id", ondelete="CASCADE"), nullable=False
    )
    reference_designator: Mapped[str] = mapped_column(String(50), nullable=False)
    footprint_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    library_entry_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    position_x: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    position_y: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    rotation_degrees: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class Layer(Base, UUIDPKMixin):
    __tablename__ = "layers"

    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    layer_type: Mapped[str] = mapped_column(String(50), nullable=False)
    visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    color: Mapped[str] = mapped_column(String(20), nullable=False, default="#000000")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
