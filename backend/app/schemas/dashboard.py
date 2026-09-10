"""Dashboard response shapes. Every breakdown here is aggregate-only (by dock
/ shift / behavior) — per the README's privacy requirement, nothing here is
ever keyed by an individual tracking ID."""
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_events: int
    events_by_risk_level: dict[str, int]
    events_by_dock: dict[str, int]
    events_by_behavior: dict[str, int]
    active_alerts: int
    escalated_alerts: int
    total_estimated_exposure_inr: float


class TrainingGapItem(BaseModel):
    dock: str
    shift: str
    behavior: str
    count: int


class TrainingGapResponse(BaseModel):
    items: list[TrainingGapItem]
