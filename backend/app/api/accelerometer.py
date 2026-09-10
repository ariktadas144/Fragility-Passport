"""Accelerometer logging endpoint -- receives phone sensor readings from
frontend/public/accelerometer.html during the live drop-test demo (Phase 2,
in-person final only).

This is the one piece of Workstream 5's original API that survived the merge
into Workstream 4's backend -- nothing on that side covers phone telemetry.
It's deliberately storage-light: readings are appended to a JSONL file per
`job_id` (a free-text label the operator types into the demo page), so the
dashboard can later show the phone-measured impact next to the pipeline's
own video-estimated impact force.

Routes are mounted under /api/accelerometer to match the URL the (frozen)
demo page already posts to; the rest of this backend has no /api prefix.
"""
import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/accelerometer", tags=["accelerometer"])

# Kept out of data/processed/ (the ML pipeline's scratch area, keyed by clip
# name) -- accelerometer logs are keyed by the demo's job label instead.
_LOG_DIR = Path(__file__).resolve().parents[3] / "data" / "accelerometer"

_SAFE_JOB_ID = re.compile(r"[^A-Za-z0-9_.-]")


def _log_path(job_id: str) -> Path:
    safe = _SAFE_JOB_ID.sub("_", job_id).strip("._-")
    if not safe:
        raise HTTPException(status_code=422, detail="Invalid job_id")
    return _LOG_DIR / f"{safe}.jsonl"


@router.post("/{job_id}")
async def log_accelerometer(job_id: str, reading: dict):
    path = _log_path(job_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(reading) + "\n")
    return {"status": "logged", "job_id": job_id}


@router.get("/{job_id}")
async def get_accelerometer_readings(job_id: str):
    path = _log_path(job_id)
    if not path.exists():
        return {"job_id": job_id, "readings": []}
    readings = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                readings.append(json.loads(line))
    return {"job_id": job_id, "readings": readings}
