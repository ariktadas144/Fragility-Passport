"""
Event/results retrieval -- reads what api/videos.py's pipeline produced.
Matches the README's documented `GET /events/{event_id}` shape, backed
by the job results on disk for now (swap for real DB query once the
event/evidence models are implemented).
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException
import json

router = APIRouter()

BASE_DIR = Path(__file__).parent.parent.parent.parent
RESULTS_DIR = BASE_DIR / "data" / "processed"


@router.get("/events/{job_id}")
async def get_job_events(job_id: str):
    summary_path = RESULTS_DIR / job_id / "summary.json"
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail="Results not ready or job not found")
    with open(summary_path) as f:
        return json.load(f)
