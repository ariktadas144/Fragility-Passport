"""Alert lifecycle: auto-created for risky events, acknowledged by a
supervisor, or auto-escalated if nobody acknowledges it in time. This is the
direct fix for the master plan's clip where a supervisor-like figure was
present and still missed a mishandling event — the system stops depending
on a human noticing in time."""
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.alert import Alert
from app.models.event import Event
from app.utils.timestamps import utcnow

# LOW-risk events are still logged as Events; they just don't page anyone.
ALERT_WORTHY_LEVELS = {"MEDIUM", "HIGH", "CRITICAL"}
AUTO_ESCALATE_LEVELS = {"HIGH", "CRITICAL"}


def create_alert_if_needed(db: Session, event: Event) -> Alert | None:
    if event.risk_level not in ALERT_WORTHY_LEVELS:
        return None
    alert = Alert(event_id=event.id, status="ACTIVE")
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def acknowledge_alert(db: Session, alert_id: int, acknowledged_by: str) -> Alert:
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise NotFoundError(f"Alert {alert_id} not found")
    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_at = utcnow()
    alert.acknowledged_by = acknowledged_by
    db.commit()
    db.refresh(alert)
    return alert


def escalate_alert(db: Session, alert_id: int) -> Alert:
    """Manual escalation (e.g. a supervisor forwarding it up the chain)."""
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise NotFoundError(f"Alert {alert_id} not found")
    alert.status = "ESCALATED"
    alert.escalated_at = utcnow()
    db.commit()
    db.refresh(alert)
    return alert


def escalate_stale_alerts(db: Session, escalation_seconds: int) -> list[Alert]:
    """Called on a timer (see main.py's background task). Any ACTIVE alert on
    a HIGH/CRITICAL event older than escalation_seconds flips to ESCALATED."""
    cutoff = utcnow() - timedelta(seconds=escalation_seconds)

    stale = (
        db.query(Alert)
        .join(Event, Alert.event_id == Event.id)
        .filter(Alert.status == "ACTIVE")
        .filter(Event.risk_level.in_(AUTO_ESCALATE_LEVELS))
        .filter(Alert.created_at <= cutoff)
        .all()
    )
    for alert in stale:
        alert.status = "ESCALATED"
        alert.escalated_at = utcnow()
    if stale:
        db.commit()
    return stale


def list_alerts(db: Session, status: str | None = None) -> list[Alert]:
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.status == status)
    return query.order_by(Alert.created_at.desc()).all()
