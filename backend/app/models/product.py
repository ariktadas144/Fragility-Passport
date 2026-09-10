from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(64))
    # Industry-indicative declared value used only for the ₹ exposure estimate
    # (docs/risk-engine.md) — not an audited price.
    declared_value_inr: Mapped[float] = mapped_column(Float, default=0.0)

    passport: Mapped["FragilityPassport | None"] = relationship(
        back_populates="product", uselist=False, cascade="all, delete-orphan"
    )
    events: Mapped[list["Event"]] = relationship(back_populates="product")
