from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class EventBehavior(Base):
    """Event <-> Behavior association. A dedicated table (rather than a bare
    many-to-many) because the master plan's evidence confirmed multi-label
    events are real (e.g. 'throwing' + 'strap misuse' on the same timestamp),
    so the schema must support 2+ concurrent tags per event."""

    __tablename__ = "event_behaviors"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    behavior_id: Mapped[int] = mapped_column(ForeignKey("behaviors.id"))

    event: Mapped["Event"] = relationship(back_populates="behavior_links")
    behavior: Mapped["Behavior"] = relationship(back_populates="event_links")
