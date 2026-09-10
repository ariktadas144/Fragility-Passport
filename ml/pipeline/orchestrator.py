"""Top-level 'process one warehouse clip' flow.

    detection + tracking   (ml/pipeline/video_pipeline.py)
      -> per-track kinematics + risk classification
                             (ml/behavior/kinetic.py, ml/vlm/classifier.py)
      -> Gemini whole-video semantic analysis
                             (ml/vlm/gemini_analysis.py)
      -> cross-validation fusion
                             (ml/behavior/fusion.py)
      -> POST each fused event to the backend
                             (ml/pipeline/backend_client.py -> POST /events)

This is the logic that used to live inline in Workstream 5's own
backend/app/api/videos.py. That standalone API is gone -- the backend is now
Workstream 4's (docs/ml-backend-contract.md), and this module is a
standalone entry point: run it as a script, or import run_and_submit() from
a job runner / future upload endpoint.

CLI:
    python -m ml.pipeline.orchestrator CLIP.mp4 --dock 06 --product-sku MATTRESS-001
    python -m ml.pipeline.orchestrator CLIP.mp4 --no-submit      # fusion only, no POST
"""
import argparse
import json
import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ml.behavior.fusion import fuse_events, prepare_gemini_events_for_fusion
from ml.behavior.kinetic import compute_kinematics, group_tracks
from ml.pipeline import backend_client
from ml.pipeline.video_pipeline import run_pipeline
from ml.vlm.classifier import classify_event
from ml.vlm.gemini_analysis import analyze_video

logger = logging.getLogger(__name__)


def _default_output_dir(video_path: str) -> Path:
    return _REPO_ROOT / "data" / "processed" / Path(video_path).stem


def run_fusion(video_path: str, output_dir: Path) -> dict:
    """Run the two detection signals and fuse them. No network calls to the
    backend -- returns the fused event log plus metadata."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Signal 1: kinematics (fast, free, physics-based) ---
    result = run_pipeline(video_path, str(output_dir))
    grouped = group_tracks(result["events"])

    kinematic_events = []
    for track_id, track_events in grouped["tracks"].items():
        kinematics = compute_kinematics(result["events"], track_id)
        if not kinematics:
            continue
        classification = classify_event(kinematics)
        if classification["risk_level"] == "low":
            continue
        kinematic_events.append({
            "track_id": track_id,
            "start_time": track_events[0]["time_sec"],
            "end_time": track_events[-1]["time_sec"],
            "class_name": track_events[0]["class_name"],
            **classification,
        })

    # --- Signal 2: Gemini whole-video analysis (graceful fallback) ---
    gemini_events_raw: list[dict] = []
    gemini_error = None
    try:
        gemini_events_raw = analyze_video(video_path).get("events", [])
    except Exception as exc:  # noqa: BLE001 -- a bad external API must not sink the job
        gemini_error = str(exc)
        logger.warning("Gemini analysis unavailable; continuing kinematics-only: %s", exc)

    gemini_events = prepare_gemini_events_for_fusion(gemini_events_raw)
    fused = fuse_events(kinematic_events, gemini_events)

    return {
        "clip": Path(video_path).name,
        "meta": result["meta"],
        "annotated_video_path": result["annotated_video_path"],
        "kinematic_event_count": len(kinematic_events),
        "gemini_event_count": len(gemini_events),
        "gemini_error": gemini_error,
        "fused_events": fused,
        "fused_event_count": len(fused),
        "confirmed_both_count": sum(1 for e in fused if e["source"] == "confirmed_both"),
    }


def run_and_submit(
    video_path: str,
    *,
    dock: str | None = None,
    product_sku: str | None = None,
    backend_url: str | None = None,
    output_dir: str | Path | None = None,
    submit: bool = True,
) -> dict:
    """Full flow: fuse, then POST every fused event to the backend's /events.

    Returns run_fusion()'s dict plus `submission_results` (per-event, from
    backend_client.submit_fused_events) and `ingested_count`.
    """
    video_path = str(video_path)
    out_dir = Path(output_dir) if output_dir else _default_output_dir(video_path)
    fusion = run_fusion(video_path, out_dir)

    # A debug/audit artifact -- NOT a parallel API. The backend is the system
    # of record now; this is just here so a failed run is inspectable.
    (out_dir / "fusion_debug.json").write_text(json.dumps(fusion, indent=2, default=str))

    submission_results: list[dict] = []
    if submit:
        if not backend_client.check_backend(backend_url):
            logger.error(
                "Backend not reachable at %s -- skipping submission. "
                "Start it with `cd backend && uvicorn app.main:app --reload`.",
                backend_client._base_url(backend_url),
            )
        else:
            submission_results = backend_client.submit_fused_events(
                fusion["fused_events"],
                source_clip_ref=Path(video_path).name,
                dock=dock,
                product_sku=product_sku,
                base_url=backend_url,
            )

    ingested = sum(1 for r in submission_results if r.get("ok"))
    logger.info("Backend ingest: %d/%d fused events accepted", ingested, len(submission_results))

    return {**fusion, "submission_results": submission_results, "ingested_count": ingested}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("video_file", type=Path, help="Warehouse clip to process")
    parser.add_argument("--dock", default=None, help="Dock identifier to tag every event with")
    parser.add_argument("--product-sku", default=None,
                        help="Product SKU (enables Fragility Passport contract checks + INR exposure)")
    parser.add_argument("--backend-url", default=None,
                        help="Backend base URL (default: $BACKEND_URL or http://localhost:8000)")
    parser.add_argument("--output-dir", default=None, help="Where to write pipeline artifacts")
    parser.add_argument("--no-submit", action="store_true", help="Run fusion only; do not POST to the backend")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if not args.video_file.is_file():
        parser.error(f"No such file: {args.video_file}")

    outcome = run_and_submit(
        str(args.video_file),
        dock=args.dock,
        product_sku=args.product_sku,
        backend_url=args.backend_url,
        output_dir=args.output_dir,
        submit=not args.no_submit,
    )

    print(json.dumps({
        "clip": outcome["clip"],
        "frames_processed": outcome["meta"]["frames_processed"],
        "kinematic_event_count": outcome["kinematic_event_count"],
        "gemini_event_count": outcome["gemini_event_count"],
        "gemini_error": outcome["gemini_error"],
        "fused_event_count": outcome["fused_event_count"],
        "confirmed_both_count": outcome["confirmed_both_count"],
        "ingested_count": outcome["ingested_count"],
    }, indent=2))

    if not args.no_submit and outcome["fused_event_count"] and outcome["ingested_count"] == 0:
        logger.error("No events reached the backend -- see errors above.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
