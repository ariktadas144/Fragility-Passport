from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.utils.timestamps import utcnow


class Evidence(Base):
    """A timestamped frame or clip backing up an Event. Used by report_service
    to embed the evidence image in the auto-generated claim packet."""

    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    file_path: Mapped[str] = mapped_column(String(512))
    kind: Mapped[str] = mapped_column(String(16), default="frame")  # "frame" | "clip"
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    event: Mapped["Event"] = relationship(back_populates="evidence_items")
