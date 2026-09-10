"""Supervisor Q&A: POST /assistant/query. See assistant_service for the
refuse -> local-lookup -> AI-fallback routing logic. No real ReasoningClient
is injected yet (Workstream 2's job) — answer_question() defaults to the
honest NullReasoningClient stub for anything it can't answer locally."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.assistant import AssistantAnswer, AssistantQuery
from app.services import assistant_service

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/query", response_model=AssistantAnswer)
def query_assistant(payload: AssistantQuery, db: Session = Depends(get_db)):
    return assistant_service.answer_question(db, payload.question)
