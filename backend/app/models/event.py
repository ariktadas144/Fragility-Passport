from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.utils.timestamps import utcnow


class Event(Base):
    """A single risk incident: one behavior (or a multi-label set, via
    EventBehavior) observed on one product, at one dock, in one time window.
    Produced by event_service.ingest_detection() from a raw ML/VLM detection."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # e.g. "EVT_001"

    video_id: Mapped[int | None] = mapped_column(ForeignKey("videos.id"), nullable=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)

    dock: Mapped[str | None] = mapped_column(String(32), nullable=True)
    start_time_seconds: Mapped[float] = mapped_column(Float)
    end_time_seconds: Mapped[float] = mapped_column(Float)

    # Calibrated by risk_service; may differ from what the ML/VLM layer sent.
    risk_level: Mapped[str] = mapped_column(String(16))
    risk_score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), default="observed_behaviour")

    evidence_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    potential_consequence: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded list
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    contract_clause_violated: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Industry-indicative estimate only — see docs/risk-engine.md.
    estimated_exposure_inr: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    video: Mapped["Video | None"] = relationship(back_populates="events")
    product: Mapped["Product | None"] = relationship(back_populates="events")
    behavior_links: Mapped[list["EventBehavior"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    evidence_items: Mapped[list["Evidence"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="event", cascade="all, delete-orphan")
