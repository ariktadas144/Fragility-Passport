"""Alert list + supervisor actions: acknowledge, or manually escalate.
Auto-escalation of stale alerts runs separately, as a background task
started in main.py (see alert_service.escalate_stale_alerts)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.exceptions import DomainError
from app.database.database import get_db
from app.schemas.alert import AlertAcknowledge, AlertRead
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertRead])
def list_alerts(status: str | None = None, db: Session = Depends(get_db)):
    return alert_service.list_alerts(db, status=status)


@router.post("/{alert_id}/acknowledge", response_model=AlertRead)
def acknowledge_alert(alert_id: int, payload: AlertAcknowledge, db: Session = Depends(get_db)):
    try:
        return alert_service.acknowledge_alert(db, alert_id, payload.acknowledged_by)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/{alert_id}/escalate", response_model=AlertRead)
def escalate_alert(alert_id: int, db: Session = Depends(get_db)):
    try:
        return alert_service.escalate_alert(db, alert_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
