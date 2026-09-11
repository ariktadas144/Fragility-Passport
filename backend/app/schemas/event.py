"""Response shapes for /events. Contrast with schemas/detection.py, which is
the inbound raw-detection contract — this is what a persisted, risk-scored
Event looks like going back OUT to the dashboard/assistant/reports."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.product import ProductRead


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_id: str
    video_id: int | None
    dock: str | None
    start_time_seconds: float
    end_time_seconds: float

    risk_level: str
    risk_score: float
    confidence: float
    status: str

    evidence_description: str | None
    recommended_action: str | None
    contract_clause_violated: str | None
    estimated_exposure_inr: float | None

    created_at: datetime

    behaviors: list[str] = []
    potential_consequence: list[str] = []
    product: ProductRead | None = None
    evidence_paths: list[str] = []


class EventListItem(BaseModel):
    """Slimmer shape for list views (dashboard timeline, assistant answers)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    public_id: str
    dock: str | None
    start_time_seconds: float
    risk_level: str
    risk_score: float
    status: str
    behaviors: list[str] = []
