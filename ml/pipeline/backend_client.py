"""Bridge: fused ML/VLM detections -> POST /events on the Workstream 4 backend.

The pipeline (video_pipeline -> kinetic -> gemini_analysis -> fusion) produces
a list of fused events. This module translates each one into the backend's
`DetectionIn` shape (see docs/ml-backend-contract.md and
backend/app/schemas/detection.py) and POSTs it to `/events`, where the risk
engine recalibrates it against the product's Fragility Passport, writes the
Event, and auto-creates an Alert if the final risk is MEDIUM+.

Resilience: one bad event never sinks the batch. Validation errors (422),
HTTP failures, and connection errors are logged and skipped;
`submit_fused_events` returns a per-event result list so the caller can see
exactly what landed and what didn't.

Configuration (all optional, sensible local-dev defaults):
  BACKEND_URL      base URL of the backend        (default http://localhost:8000)
  BACKEND_API_KEY  X-API-Key header value         (default: none; only needed
                                                   if the backend sets API_KEY)
"""
import logging
import os

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://localhost:8000"

# Fallback map for kinematic-classifier behavior strings that aren't already
# backend BEHAVIOR_CODES. ml/vlm/classifier.py emits codes directly now, but
# older values / a swapped-in classifier shouldn't 422 the whole event.
_KINEMATIC_BEHAVIOR_TO_CODE = {
    "product_dropped": "product_dropped",
    "product_dragged": "product_dragged",
    "dropping": "product_dropped",
    "dragging": "product_dragged",
    "rolling": "product_rolling",
    "rough_handling": "rough_handling",
}


def _base_url(explicit: str | None = None) -> str:
    return (explicit or os.environ.get("BACKEND_URL") or DEFAULT_BASE_URL).rstrip("/")


def _api_key(explicit: str | None = None) -> str | None:
    return explicit or os.environ.get("BACKEND_API_KEY") or None


def _behavior_codes_for(fused_event: dict) -> list[str]:
    vlm = fused_event.get("vlm_signal")
    if vlm and vlm.get("behavior"):
        return list(vlm["behavior"])

    kin = fused_event.get("kinematic_signal")
    if kin and kin.get("behavior") and kin["behavior"] != "normal":
        raw = kin["behavior"]
        code = _KINEMATIC_BEHAVIOR_TO_CODE.get(raw)
        if code:
            return [code]
        logger.warning("No behavior-code mapping for kinematic behavior %r; using 'rough_handling'", raw)
        return ["rough_handling"]

    return []


def _overlap_duration_seconds(fused_event: dict) -> float | None:
    """For confirmed_both events, how many seconds the kinematics window and
    the Gemini window actually overlap -- a cheap, honest confidence signal."""
    k = fused_event.get("kinematic_signal")
    v = fused_event.get("vlm_signal")
    if not (k and v and "_start_sec" in v and "_end_sec" in v):
        return None
    start = max(k["start_time"], v["_start_sec"])
    end = min(k["end_time"], v["_end_sec"])
    return round(max(0.0, end - start), 3)


def fused_event_to_detection(
    fused_event: dict,
    *,
    source_clip_ref: str | None = None,
    dock: str | None = None,
    product_sku: str | None = None,
    video_id: int | None = None,
) -> dict | None:
    """Translate one ml.behavior.fusion.fuse_events() item into a DetectionIn
    dict. Returns None if the event carries no usable behavior code (nothing
    to report)."""
    behavior = _behavior_codes_for(fused_event)
    if not behavior:
        logger.warning("Skipping fused event (%s) with no usable behavior code", fused_event.get("source"))
        return None

    vlm = fused_event.get("vlm_signal") or {}
    kin = fused_event.get("kinematic_signal") or {}
    source = fused_event.get("source", "")

    confidence = vlm.get("confidence")
    if confidence is None:
        # No semantic confirmation: a bare physics flag. confirmed_both without
        # a VLM confidence shouldn't happen, but score it a touch higher if so.
        confidence = 0.6 if source == "confirmed_both" else 0.5

    event_id = vlm.get("event_id")
    if not event_id and kin.get("track_id") is not None:
        event_id = f"KIN_{kin['track_id']}"

    detection = {
        "event_id": event_id,
        "video_id": video_id,
        "source_clip_ref": source_clip_ref,
        "dock": dock,
        "product_sku": product_sku,
        "start_time": round(float(fused_event["start_time"]), 3),
        "end_time": round(float(fused_event["end_time"]), 3),
        "behavior": behavior,
        "risk_level": fused_event.get("risk_level"),
        "risk_score": vlm.get("risk_score"),
        "confidence": round(float(confidence), 3),
        "evidence": vlm.get("evidence") or kin.get("explanation"),
        "potential_consequence": vlm.get("potential_consequence"),
        "recommended_action": vlm.get("recommended_action"),
        "status": vlm.get("status", "observed_behaviour"),
        # Kinetic fields: pass ONLY real measured values. Pixel-space velocity
        # is not m/s, so velocity_mps / impact_deceleration_mps2 stay null
        # until the accelerometer-calibrated impact work (Workstream 5, task 2).
        "tilt_deg": kin.get("tilt_deg"),
        "drop_height_cm": kin.get("drop_height_cm"),
        "velocity_mps": kin.get("velocity_mps"),
        "impact_deceleration_mps2": kin.get("impact_deceleration_mps2"),
        "overlap_duration_seconds": _overlap_duration_seconds(fused_event),
    }
    # Strip None so the backend applies its own defaults / fallbacks cleanly.
    return {key: value for key, value in detection.items() if value is not None}


def check_backend(base_url: str | None = None, timeout: float = 5.0) -> bool:
    """True if the backend's /health responds 200."""
    url = f"{_base_url(base_url)}/health"
    try:
        return httpx.get(url, timeout=timeout).status_code == 200
    except httpx.HTTPError as exc:
        logger.warning("Backend health check failed (%s): %s", url, exc)
        return False


def submit_fused_events(
    fused_events: list[dict],
    *,
    source_clip_ref: str | None = None,
    dock: str | None = None,
    product_sku: str | None = None,
    video_id: int | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    timeout: float = 30.0,
) -> list[dict]:
    """POST every fused event to /events. Never raises for a single bad
    event -- logs and continues. Returns a result dict per input event:

        {"index": int, "ok": True,  "backend_event": {...}}          success
        {"index": int, "ok": False, "skipped": True, "reason": ...}  no behavior code
        {"index": int, "ok": False, "status_code": 422, ...}         backend rejected it
        {"index": int, "ok": False, "error": "..."}                  connection/HTTP error
    """
    base = _base_url(base_url)
    key = _api_key(api_key)
    headers = {"X-API-Key": key} if key else {}
    url = f"{base}/events"

    results: list[dict] = []
    with httpx.Client(timeout=timeout) as client:
        for index, fused_event in enumerate(fused_events):
            detection = fused_event_to_detection(
                fused_event,
                source_clip_ref=source_clip_ref,
                dock=dock,
                product_sku=product_sku,
                video_id=video_id,
            )
            if detection is None:
                results.append({"index": index, "ok": False, "skipped": True,
                                "reason": "no usable behavior code"})
                continue

            try:
                resp = client.post(url, json=detection, headers=headers)
            except httpx.HTTPError as exc:
                logger.error("POST %s failed for %s: %s", url, detection.get("event_id"), exc)
                results.append({"index": index, "ok": False, "error": str(exc),
                                "detection": detection})
                continue

            if resp.status_code >= 400:
                logger.error("POST /events -> %s for %s: %s",
                             resp.status_code, detection.get("event_id"), resp.text[:500])
                results.append({"index": index, "ok": False,
                                "status_code": resp.status_code,
                                "response": resp.text[:500], "detection": detection})
                continue

            body = resp.json()
            logger.info(
                "Ingested %s -> backend id=%s risk=%s/%s exposure=%s clause=%s",
                detection.get("event_id"), body.get("id"), body.get("risk_level"),
                body.get("risk_score"), body.get("estimated_exposure_inr"),
                bool(body.get("contract_clause_violated")),
            )
            results.append({"index": index, "ok": True, "backend_event": body})

    return results
