"""POST /events is the ML/VLM pipeline's front door into the backend — see
docs/ml-backend-contract.md for the full JSON shape. Everything after
schema validation is delegated to event_service.ingest_detection(), so this
file stays a thin HTTP wrapper: parse request -> call service -> translate
domain errors to HTTP status codes -> return."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.exceptions import DomainError
from app.core.security import require_api_key
from app.database.database import get_db
from app.schemas.detection import DetectionIn
from app.schemas.event import EventListItem, EventRead
from app.services import event_service

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventRead, dependencies=[Depends(require_api_key)])
def ingest_event(payload: DetectionIn, db: Session = Depends(get_db)):
    try:
        event = event_service.ingest_detection(db, payload)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return event_service.to_event_read_dict(event)


@router.get("", response_model=list[EventListItem])
def list_events(dock: str | None = None, risk_level: str | None = None, db: Session = Depends(get_db)):
    events = event_service.list_events(db, dock=dock, risk_level=risk_level)
    return [event_service.to_event_read_dict(e) for e in events]


@router.get("/{event_id}", response_model=EventRead)
def get_event(event_id: int, db: Session = Depends(get_db)):
    try:
        event = event_service.get_event(db, event_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return event_service.to_event_read_dict(event)
