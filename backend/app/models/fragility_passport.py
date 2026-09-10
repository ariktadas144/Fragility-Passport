from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class FragilityPassport(Base):
    """The machine-readable 'handling contract' for one product class:
    max safe drop height, max tilt angle, required orientation, max stack
    weight, drag/throw tolerance. This is what the loading-bay camera checks
    real behavior against."""

    __tablename__ = "fragility_passports"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), unique=True)

    max_tilt_deg: Mapped[float] = mapped_column(Float, default=90.0)
    max_drop_height_cm: Mapped[float] = mapped_column(Float, default=0.0)
    required_orientation: Mapped[str] = mapped_column(String(16), default="ANY")
    max_stack_weight_kg: Mapped[float] = mapped_column(Float, default=0.0)
    drag_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    throw_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="passport")
