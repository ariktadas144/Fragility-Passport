from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.utils.timestamps import utcnow


class Alert(Base):
    """A live notification tied to one Event. Created automatically when an
    Event's risk is MEDIUM or above. If nobody acknowledges it within
    ESCALATION_SECONDS, the background task in main.py flips it to ESCALATED
    (this is the 'supervisor was standing right there and still missed it'
    problem from the master plan — the system stops depending on a human
    noticing in time)."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")  # ACTIVE | ACKNOWLEDGED | ESCALATED

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    event: Mapped["Event"] = relationship(back_populates="alerts")
