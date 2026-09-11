"""POST /pipeline/upload -- the live-demo entry point. A judge/teammate
uploads a clip; it's saved to data/uploads/ and the existing ML orchestrator
(ml/pipeline/orchestrator.run_and_submit) runs it in a background thread,
POSTing the fused events straight into this backend's /events. The response
returns immediately; results appear on the dashboard / incidents pages once
the run finishes (~1-3 min for a short clip)."""
import sys
import threading
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.logging import get_logger

# ml/ lives at the repo root, one level above backend/.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ml.pipeline import orchestrator  # noqa: E402

logger = get_logger(__name__)
router = APIRouter(prefix="/pipeline", tags=["pipeline"])

UPLOAD_DIR = _REPO_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

_ALLOWED_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
_MAX_BYTES = 200 * 1024 * 1024  # 200 MB

# job_id -> {"status", "clip", "error", "ingested_count", ...}
JOBS: dict[str, dict] = {}


def _safe_name(filename: str | None) -> str:
    base = Path(filename or "clip.mp4").name
    base = "".join(c for c in base if c.isalnum() or c in "._- ").strip() or "clip.mp4"
    return base


def _run_job(job_id: str, video_path: str, dock: str | None, product_sku: str | None) -> None:
    JOBS[job_id]["status"] = "processing"
    try:
        outcome = orchestrator.run_and_submit(
            video_path, dock=dock or None, product_sku=product_sku or None
        )
        JOBS[job_id].update(
            status="done",
            fused_event_count=outcome["fused_event_count"],
            ingested_count=outcome["ingested_count"],
            gemini_error=outcome["gemini_error"],
        )
        logger.info("Pipeline job %s done: %d events ingested", job_id, outcome["ingested_count"])
    except Exception as exc:  # noqa: BLE001 -- surface any failure on the job, don't crash the thread
        JOBS[job_id].update(status="failed", error=str(exc))
        logger.warning("Pipeline job %s failed: %s", job_id, exc)


@router.post("/upload")
async def upload_and_process(
    file: UploadFile = File(...),
    dock: str | None = Form(default=None),
    product_sku: str | None = Form(default=None),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{suffix or '(none)'}'. Allowed: {', '.join(sorted(_ALLOWED_SUFFIXES))}",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(data) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large ({len(data) / 1e6:.0f} MB); limit is 200 MB.")

    job_id = uuid.uuid4().hex[:8]
    dest = UPLOAD_DIR / f"{job_id}_{_safe_name(file.filename)}"
    dest.write_bytes(data)

    JOBS[job_id] = {"status": "queued", "clip": dest.name}
    threading.Thread(
        target=_run_job, args=(job_id, str(dest), dock, product_sku), daemon=True
    ).start()

    return {"job_id": job_id, "status": "processing", "clip": dest.name}


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **job}
