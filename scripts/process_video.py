#!/usr/bin/env python3
"""Adapter between the ML pipeline's output and the backend. Once
ml/pipeline/video_pipeline.py exists and writes its detections as JSON in
the documented shape (docs/ml-backend-contract.md), this script pushes them
into the backend the same way a live POST /events call would — real risk
scoring, real alerts. It does not import any ml/* code directly, so
Workstream 4 and the DS/ML workstream can be built independently against
the shared JSON contract.

Usage:
  python scripts/process_video.py video.mp4 pipeline_output.json \\
      [--dock DOCK] [--duration-seconds N] [--fps N]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from pydantic import ValidationError  # noqa: E402

from app.database.database import SessionLocal, init_db  # noqa: E402
from app.models.video import Video  # noqa: E402
from app.schemas.detection import DetectionIn  # noqa: E402
from app.services import event_service  # noqa: E402


def _get_or_create_video(db, filename: str, dock: str | None, duration_seconds: float | None, fps: float | None) -> Video:
    video = db.query(Video).filter(Video.source_clip_ref == filename).first()
    if video is not None:
        return video
    video = Video(
        filename=filename,
        source_clip_ref=filename,
        dock=dock,
        duration_seconds=duration_seconds,
        fps=fps,
        status="processed",
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video_file", type=Path, help="The source video the pipeline processed (its filename is used as the join key)")
    parser.add_argument("pipeline_output", type=Path, help="JSON file of detections: a list, or {'events': [...]}")
    parser.add_argument("--dock", default=None)
    parser.add_argument("--duration-seconds", type=float, default=None)
    parser.add_argument("--fps", type=float, default=None)
    args = parser.parse_args()

    data = json.loads(args.pipeline_output.read_text())
    raw_events = data if isinstance(data, list) else data.get("events", [])

    init_db()
    db = SessionLocal()
    imported, skipped = 0, 0
    try:
        video = _get_or_create_video(db, args.video_file.name, args.dock, args.duration_seconds, args.fps)
        for raw_event in raw_events:
            raw_event = dict(raw_event)
            raw_event["video_id"] = video.id
            raw_event.setdefault("dock", args.dock)
            try:
                payload = DetectionIn(**raw_event)
            except ValidationError as exc:
                print(f"Skipping invalid detection {raw_event.get('event_id', '?')}: {exc}", file=sys.stderr)
                skipped += 1
                continue
            event_service.ingest_detection(db, payload)
            imported += 1
    finally:
        db.close()

    print(f"Video '{args.video_file.name}': imported {imported} detection(s), skipped {skipped}.")


if __name__ == "__main__":
    main()
