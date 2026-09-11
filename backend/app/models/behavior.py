from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Behavior(Base):
    """One entry from the fixed behavior vocabulary (app.core.constants).
    Seeded once at startup; code is the stable machine-readable key the
    ML/VLM layer sends in Event.behavior[]."""

    __tablename__ = "behaviors"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(32))
    default_severity: Mapped[int] = mapped_column(Integer, default=1)

    event_links: Mapped[list["EventBehavior"]] = relationship(back_populates="behavior")
