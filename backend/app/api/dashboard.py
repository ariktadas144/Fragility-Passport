"""Aggregate-only dashboard views (dock/shift/behavior — never per worker)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.dashboard import DashboardSummary, TrainingGapResponse
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db)):
    return dashboard_service.get_summary(db)


@router.get("/training-gaps", response_model=TrainingGapResponse)
def get_training_gaps(db: Session = Depends(get_db)):
    return dashboard_service.get_training_gaps(db)
