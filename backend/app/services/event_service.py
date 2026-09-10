"""Turns a raw ML/VLM detection (schemas.DetectionIn) into a persisted,
risk-scored Event. This is the single front door every upstream source goes
through — the live pipeline via POST /events, the notebook's
warehouse_event_log.json via scripts/import_events.py, and the seed script —
so risk scoring and alerting behave identically no matter where the
detection came from."""
import json
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.behavior import Behavior
from app.models.event import Event
from app.models.event_behavior import EventBehavior
from app.models.video import Video
from app.schemas.detection import DetectionIn
from app.schemas.product import ProductRead
from app.services import alert_service, evidence_service, passport_service, risk_service
from app.utils.timestamps import parse_timecode, validate_within_duration
from app.utils.validators import dedupe_preserve_order


def _get_or_create_video(db: Session, payload: DetectionIn) -> Video | None:
    if payload.video_id is not None:
        video = db.get(Video, payload.video_id)
        if video is None:
            raise NotFoundError(f"Video {payload.video_id} not found")
        return video

    if payload.source_clip_ref is None:
        return None

    video = db.query(Video).filter(Video.source_clip_ref == payload.source_clip_ref).first()
    if video is None:
        video = Video(
            filename=payload.source_clip_ref,
            source_clip_ref=payload.source_clip_ref,
            dock=payload.dock,
            status="processed",
        )
        db.add(video)
        db.commit()
        db.refresh(video)
    return video


def _resolve_product(db: Session, payload: DetectionIn):
    if payload.product_id is not None:
        return passport_service.get_product(db, payload.product_id)
    if payload.product_sku is not None:
        return passport_service.get_product_by_sku(db, payload.product_sku)
    return None


def _resolve_behaviors(db: Session, codes: list[str]) -> list[Behavior]:
    codes = dedupe_preserve_order(codes)
    rows = db.query(Behavior).filter(Behavior.code.in_(codes)).all()
    by_code = {b.code: b for b in rows}
    # Preserve the caller's ordering (schema validation already guarantees
    # every code exists, so this should never drop anything silently).
    return [by_code[c] for c in codes if c in by_code]


def _generate_public_id() -> str:
    return f"EVT_{uuid.uuid4().hex[:8].upper()}"


def ingest_detection(db: Session, payload: DetectionIn) -> Event:
    start_seconds = parse_timecode(payload.start_time)
    end_seconds = parse_timecode(payload.end_time)

    video = _get_or_create_video(db, payload)
    validate_within_duration(start_seconds, end_seconds, video.duration_seconds if video else None)

    product = _resolve_product(db, payload)
    behaviors = _resolve_behaviors(db, payload.behavior)
    passport = passport_service.get_passport_for_product(db, product.id) if product else None

    assessment = risk_service.calibrate_risk(payload, behaviors, passport, product)

    public_id = payload.event_id or _generate_public_id()
    if db.query(Event).filter(Event.public_id == public_id).first() is not None:
        public_id = _generate_public_id()

    event = Event(
        public_id=public_id,
        video_id=video.id if video else None,
        product_id=product.id if product else None,
        dock=payload.dock or (video.dock if video else None),
        start_time_seconds=start_seconds,
        end_time_seconds=end_seconds,
        risk_level=assessment.risk_level,
        risk_score=assessment.risk_score,
        confidence=payload.confidence,
        status=payload.status,
        evidence_description=payload.evidence,
        potential_consequence=json.dumps(payload.potential_consequence or []),
        recommended_action=payload.recommended_action,
        contract_clause_violated=assessment.contract_clause_violated,
        estimated_exposure_inr=assessment.estimated_exposure_inr,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    for behavior in behaviors:
        db.add(EventBehavior(event_id=event.id, behavior_id=behavior.id))
    db.commit()

    if payload.evidence_frame_path:
        evidence_service.add_evidence(db, event.id, payload.evidence_frame_path, kind="frame")

    alert_service.create_alert_if_needed(db, event)

    db.refresh(event)
    return event


def get_event(db: Session, event_id: int) -> Event:
    event = db.get(Event, event_id)
    if event is None:
        raise NotFoundError(f"Event {event_id} not found")
    return event


def get_event_by_public_id(db: Session, public_id: str) -> Event:
    event = db.query(Event).filter(Event.public_id == public_id).first()
    if event is None:
        raise NotFoundError(f"Event {public_id} not found")
    return event


def list_events(
    db: Session, dock: str | None = None, risk_level: str | None = None, limit: int = 200
) -> list[Event]:
    query = db.query(Event)
    if dock:
        query = query.filter(Event.dock == dock)
    if risk_level:
        query = query.filter(Event.risk_level == risk_level)
    return query.order_by(Event.created_at.desc()).limit(limit).all()


def to_event_read_dict(event: Event) -> dict:
    """Builds the extra computed fields (behaviors, potential_consequence,
    evidence_paths) that schemas.EventRead needs but the ORM object doesn't
    expose directly as plain attributes."""
    return {
        "id": event.id,
        "public_id": event.public_id,
        "video_id": event.video_id,
        "dock": event.dock,
        "start_time_seconds": event.start_time_seconds,
        "end_time_seconds": event.end_time_seconds,
        "risk_level": event.risk_level,
        "risk_score": event.risk_score,
        "confidence": event.confidence,
        "status": event.status,
        "evidence_description": event.evidence_description,
        "recommended_action": event.recommended_action,
        "contract_clause_violated": event.contract_clause_violated,
        "estimated_exposure_inr": event.estimated_exposure_inr,
        "created_at": event.created_at,
        "behaviors": [link.behavior.code for link in event.behavior_links],
        "potential_consequence": json.loads(event.potential_consequence) if event.potential_consequence else [],
        "product": ProductRead.model_validate(event.product) if event.product else None,
        "evidence_paths": [e.file_path for e in event.evidence_items],
    }
