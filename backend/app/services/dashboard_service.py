"""Aggregation-only views for the dashboard. Everything here is grouped by
dock/shift/behavior — never by an individual tracking ID, per the README's
privacy requirement (tracking ID-instability was also measured to be
unreliable in the pilot benchmark, which is a second reason not to key
anything off it)."""
from collections import Counter

from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.behavior import Behavior
from app.models.event import Event
from app.models.event_behavior import EventBehavior
from app.schemas.dashboard import DashboardSummary, TrainingGapItem, TrainingGapResponse


def _shift_for_hour(hour: int) -> str:
    """A simple two-shift split on the event's UTC hour. Swap for a real
    shift calendar once the warehouse's actual shift times are known."""
    return "morning" if 6 <= hour < 18 else "evening"


def get_summary(db: Session) -> DashboardSummary:
    events = db.query(Event).all()

    events_by_risk_level = Counter(e.risk_level for e in events)
    events_by_dock = Counter(e.dock or "unknown" for e in events)

    behavior_labels = (
        db.query(Behavior.label).join(EventBehavior, EventBehavior.behavior_id == Behavior.id).all()
    )
    events_by_behavior = Counter(label for (label,) in behavior_labels)

    active_alerts = db.query(Alert).filter(Alert.status == "ACTIVE").count()
    escalated_alerts = db.query(Alert).filter(Alert.status == "ESCALATED").count()

    total_exposure = sum(e.estimated_exposure_inr or 0.0 for e in events)

    return DashboardSummary(
        total_events=len(events),
        events_by_risk_level=dict(events_by_risk_level),
        events_by_dock=dict(events_by_dock),
        events_by_behavior=dict(events_by_behavior),
        active_alerts=active_alerts,
        escalated_alerts=escalated_alerts,
        total_estimated_exposure_inr=round(total_exposure, 2),
    )


def get_training_gaps(db: Session) -> TrainingGapResponse:
    """e.g. "Dock 09 evening shift: 3x dragging incidents vs. morning shift"
    — the master plan's Tier 2 training-gap dashboard feature."""
    rows = (
        db.query(Event.dock, Event.created_at, Behavior.label)
        .join(EventBehavior, EventBehavior.event_id == Event.id)
        .join(Behavior, Behavior.id == EventBehavior.behavior_id)
        .all()
    )

    counts: Counter[tuple[str, str, str]] = Counter()
    for dock, created_at, label in rows:
        shift = _shift_for_hour(created_at.hour)
        counts[(dock or "unknown", shift, label)] += 1

    items = [
        TrainingGapItem(dock=dock, shift=shift, behavior=behavior, count=count)
        for (dock, shift, behavior), count in sorted(counts.items(), key=lambda kv: -kv[1])
    ]
    return TrainingGapResponse(items=items)
