"""
Video upload + processing endpoint -- the live-upload demo entry point.
A judge/teammate uploads a clip, this kicks off BOTH pipelines in the
background (kinematics from tracking, and Gemini whole-video analysis),
fuses their results, and returns a job_id to poll for results via
api/events.py.
"""

import uuid
import shutil
import threading
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
import json

from ml.pipeline.video_pipeline import run_pipeline
from ml.behavior.kinetic import compute_kinematics, group_tracks
from ml.behavior.fusion import fuse_events, prepare_gemini_events_for_fusion
from ml.vlm.classifier import classify_event
from ml.vlm.gemini_analysis import analyze_video

router = APIRouter()

BASE_DIR = Path(__file__).parent.parent.parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
RESULTS_DIR = BASE_DIR / "data" / "processed"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory job store -- swap for the real DB (event/video models) when ready.
# Every endpoint here reads/writes through this dict, so the swap is contained
# to this one file.
JOBS = {}


def _process_video(job_id: str, video_path: str):
    JOBS[job_id]["status"] = "processing"
    try:
        out_dir = RESULTS_DIR / job_id

        # --- Signal 1: kinematics (fast, free, motion-based) ---
        result = run_pipeline(video_path, str(out_dir))
        grouped = group_tracks(result["events"])
        by_track = grouped["tracks"]

        kinematic_events = []
        for track_id, track_events in by_track.items():
            kinematics = compute_kinematics(result["events"], track_id)
            if not kinematics:
                continue
            classification = classify_event(kinematics)
            if classification["risk_level"] != "low":
                kinematic_events.append({
                    "track_id": track_id,
                    "start_time": track_events[0]["time_sec"],
                    "end_time": track_events[-1]["time_sec"],
                    "class_name": track_events[0]["class_name"],
                    **classification,
                })

        # --- Signal 2: Gemini whole-video semantic analysis ---
        # Wrapped defensively: if there's no API key, or Gemini's API fails
        # (rate limit, network, bad output), fall back to kinematics-only
        # rather than failing the whole job. This is the resilience story --
        # a live demo shouldn't go down because one external API had a bad
        # moment.
        gemini_events_raw = []
        gemini_error = None
        try:
            gemini_result = analyze_video(video_path)
            gemini_events_raw = gemini_result.get("events", [])
        except Exception as e:
            gemini_error = str(e)

        gemini_events = prepare_gemini_events_for_fusion(gemini_events_raw)

        # --- Fusion: cross-validate the two signals ---
        fused = fuse_events(kinematic_events, gemini_events)

        summary = {
            "total_frames": result["meta"]["frames_processed"],
            "total_tracked_objects": len(by_track),
            "untracked_detections_excluded": grouped["untracked_excluded"],
            "kinematic_event_count": len(kinematic_events),
            "gemini_event_count": len(gemini_events),
            "gemini_error": gemini_error,  # None if Gemini succeeded
            "fused_events": fused,
            "fused_event_count": len(fused),
            "confirmed_both_count": sum(1 for e in fused if e["source"] == "confirmed_both"),
        }

        with open(RESULTS_DIR / job_id / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        JOBS[job_id]["status"] = "done"
        JOBS[job_id]["summary"] = summary
        JOBS[job_id]["annotated_video_path"] = result["annotated_video_path"]

    except Exception as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)


@router.post("/videos/upload")
async def upload_video(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())[:8]
    video_path = UPLOAD_DIR / f"{job_id}_{file.filename}"

    with open(video_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    JOBS[job_id] = {"status": "queued", "filename": file.filename}

    thread = threading.Thread(target=_process_video, args=(job_id, str(video_path)))
    thread.start()

    return {"job_id": job_id, "status": "queued"}


@router.get("/videos/{job_id}")
async def get_job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
