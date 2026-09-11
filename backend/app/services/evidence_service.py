"""Persists Evidence rows (frame/clip references) for an Event. Saving the
actual file to disk is app.utils.file_utils' job; this is just the database
side of it."""
from sqlalchemy.orm import Session

from app.models.evidence import Evidence


def add_evidence(db: Session, event_id: int, file_path: str, kind: str = "frame") -> Evidence:
    evidence = Evidence(event_id=event_id, file_path=file_path, kind=kind)
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def list_evidence(db: Session, event_id: int) -> list[Evidence]:
    return db.query(Evidence).filter(Evidence.event_id == event_id).order_by(Evidence.captured_at).all()
