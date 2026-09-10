"""
Accelerometer logging endpoint -- receives phone sensor readings from
frontend/public/accelerometer.html during the live drop-test demo (Phase 2,
in-person final only). Stored alongside the job's video-pipeline results so
the dashboard can show them side-by-side: phone-measured impact vs. the
pipeline's independently video-estimated impact force.
"""

from pathlib import Path
from fastapi import APIRouter
import json

router = APIRouter()

BASE_DIR = Path(__file__).parent.parent.parent.parent
RESULTS_DIR = BASE_DIR / "data" / "processed"


@router.post("/accelerometer/{job_id}")
async def log_accelerometer(job_id: str, reading: dict):
    path = RESULTS_DIR / job_id
    path.mkdir(parents=True, exist_ok=True)
    log_file = path / "accelerometer_log.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(reading) + "\n")
    return {"status": "logged"}


@router.get("/accelerometer/{job_id}")
async def get_accelerometer_readings(job_id: str):
    log_file = RESULTS_DIR / job_id / "accelerometer_log.jsonl"
    if not log_file.exists():
        return {"readings": []}
    readings = []
    with open(log_file) as f:
        for line in f:
            line = line.strip()
            if line:
                readings.append(json.loads(line))
    return {"readings": readings}
