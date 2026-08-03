import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class YDocSnapshot(Base):
    """Persisted CRDT state for a file's collaborative document.

    One row per file: `state` holds the merged Yjs update bytes
    (`Y.encode_state_as_update`), rewritten each time the last
    collaborator disconnects.
    """

    __tablename__ = "ydoc_snapshots"

    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), primary_key=True
    )
    state: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
