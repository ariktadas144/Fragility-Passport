"""
Conversational assistant endpoint -- grounded Q&A over a job's event log.
Real reasoning lives in ml/vlm/reasoning.py (currently a stub).
"""

from pathlib import Path
from fastapi import APIRouter
import json

from ml.vlm.reasoning import query_assistant

router = APIRouter()

BASE_DIR = Path(__file__).parent.parent.parent.parent
RESULTS_DIR = BASE_DIR / "data" / "processed"


@router.post("/assistant/{job_id}/ask")
async def ask_assistant(job_id: str, payload: dict):
    question = payload.get("question", "")
    summary_path = RESULTS_DIR / job_id / "summary.json"
    event_log = []
    if summary_path.exists():
        with open(summary_path) as f:
            event_log = json.load(f).get("risk_events", [])
    answer = query_assistant(question, event_log)
    return {"answer": answer}
