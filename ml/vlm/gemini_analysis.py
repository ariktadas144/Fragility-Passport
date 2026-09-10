"""
Gemini whole-video behavior analysis.

Converted from the original prototype notebook (ml/vlm/Warehouse_AI_Video_Intelligence_Notebook.ipynb)
into an importable module so backend/app/api/videos.py can call it directly
instead of running it interactively in Colab. Logic is unchanged from the
notebook -- same prompt, same validation, same handling-rules mapping.

Requires GEMINI_API_KEY. It is read from the environment; if absent, it is
loaded from backend/.env (or a repo-root .env) via python-dotenv.
"""

import os
import json
import re
import time
import cv2
from pathlib import Path

from google import genai
from google.genai import errors, types

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv is optional -- env may be populated another way
    load_dotenv = None

GEMINI_MODEL = "gemini-3.1-flash-lite"

# How long to wait for Gemini's server-side video processing to reach ACTIVE
# before giving up. Without this the poll loop below could spin forever on a
# stuck upload, hanging the whole job. Override with the env var.
_DEFAULT_VIDEO_PROCESSING_TIMEOUT_SEC = 180.0

# The Gemini Files API status endpoint intermittently returns HTTP 500s that
# have nothing to do with the file itself. Tolerate this many before failing.
_MAX_TRANSIENT_POLL_ERRORS = 5


def _load_env() -> None:
    """Populate GEMINI_API_KEY from a .env file if it's not already set.

    Checks backend/.env first (where the rest of the app keeps its secrets),
    then a repo-root .env. No-op if the key is already in the environment or
    python-dotenv isn't installed.
    """
    if os.environ.get("GEMINI_API_KEY") or load_dotenv is None:
        return
    repo_root = Path(__file__).resolve().parents[2]
    for candidate in (repo_root / "backend" / ".env", repo_root / ".env"):
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            if os.environ.get("GEMINI_API_KEY"):
                return


def _video_processing_timeout_sec() -> float:
    raw = os.environ.get("GEMINI_VIDEO_PROCESSING_TIMEOUT")
    if not raw:
        return _DEFAULT_VIDEO_PROCESSING_TIMEOUT_SEC
    try:
        return max(30.0, float(raw))
    except ValueError:
        return _DEFAULT_VIDEO_PROCESSING_TIMEOUT_SEC


# Closed vocabulary -- MUST stay in sync with the backend's
# app/core/constants.py::BEHAVIOR_VOCABULARY (14 codes). The backend's
# /events endpoint rejects any event carrying a code outside this set with a
# 422, so a mismatch here silently drops detections. The first 10 are the
# original notebook set; the last 4 were added by Workstream 4 to cover the
# ground-truth taxonomy's static/dock behaviours.
BEHAVIORS = [
    "product_dropped",
    "product_dragged",
    "product_thrown",
    "product_rolling",
    "rough_handling",
    "improper_stacking",
    "unstable_stacking",
    "product_outside_designated_area",
    "improper_equipment_usage",
    "unsafe_loading_sequence",
    "wrong_orientation",
    "stepping_on_product",
    "dock_vehicle_gap",
    "uneven_dock_level",
]

VALID_RISK = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_STATUS = {"observed_behaviour", "potential_risk", "confirmed_damage"}

HANDLING_RULES = {
    "product_dropped": ("WH-001", "Products must be lifted and placed gently; never throw or drop packages."),
    "product_dragged": ("WH-002", "Use suitable handling equipment instead of dragging products."),
    "product_thrown": ("WH-003", "Products must be handled carefully and placed in a controlled manner."),
    "product_rolling": ("WH-004", "Use appropriate material-handling equipment; do not roll unless designed for it."),
    "rough_handling": ("WH-005", "Handle every product carefully and in a controlled manner."),
    "improper_stacking": ("WH-006", "Stack heavier products at the bottom and lighter products on top."),
    "unstable_stacking": ("WH-007", "Load products in a stable configuration."),
    "product_outside_designated_area": ("WH-008", "Stage products systematically in the designated area."),
    "improper_equipment_usage": ("WH-009", "Use the correct equipment for material movement."),
    "unsafe_loading_sequence": ("WH-010", "Load products in a stable and planned sequence."),
    "wrong_orientation": ("WH-011", "Transport vertical products upright; never lay them horizontally."),
    "stepping_on_product": ("WH-012", "Never step, stand, or climb on cartons or products."),
    "dock_vehicle_gap": ("WH-013", "Bridge the dock-to-vehicle gap with a dock plate before loading."),
    "uneven_dock_level": ("WH-014", "Use a dock leveller when dock and vehicle bed heights differ."),
}


def timestamp_to_seconds(t: str) -> float:
    if not isinstance(t, str) or ":" not in t:
        raise ValueError(f"Invalid timestamp format: {t}")
    minutes, seconds = t.split(":", 1)
    return int(minutes) * 60 + float(seconds)


def _retry_options() -> "types.HttpRetryOptions":
    """A few automatic retries with exponential backoff. gemini-3.1-flash-lite
    + the Files API have been observed returning transient 500/503s on the
    video path (model overloaded, Files API blips) even when the key and
    model are fine -- retrying absorbs most of those."""
    return types.HttpRetryOptions(attempts=3, initial_delay=2.0, max_delay=30.0, exp_base=2.0)


def _get_client() -> genai.Client:
    _load_env()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable not set. "
            "Set it before calling analyze_video()."
        )
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(retry_options=_retry_options()),
    )


def _get_video_duration(video_path: str) -> float:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Could not open the video.")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    duration = frame_count / fps if fps and fps > 0 else 0.0
    if duration <= 0:
        raise RuntimeError("Could not determine video duration.")
    return duration


def _build_prompt(video_path: str, duration: float) -> str:
    return f"""
You are an AI Video Intelligence system for warehouse operations.

Analyze the uploaded warehouse video as a temporal sequence.

ACTUAL VIDEO DURATION:
{duration:.2f} seconds

TIMESTAMP REQUIREMENTS:
- Every start_time and end_time MUST be within 00:00 and {duration:.2f} seconds.
- Never invent timestamps outside the real video duration.
- Use only timestamps supported by the visible video sequence.

DETECT ONLY THESE PREDEFINED BEHAVIOURS:
{chr(10).join("- " + b for b in BEHAVIORS)}

IMPORTANT:
- Report only visually observable behaviour.
- Do not invent SKU, price, weight, injury, monetary value, identity, or other unavailable facts.
- Do not claim confirmed product damage unless actual damage is clearly visible.
- Distinguish observed behaviour, potential risk, and confirmed damage.
- Multiple behaviours may belong to the same event.
- If no predefined behaviour is visible, return an empty events array.

RETURN ONLY VALID JSON:

{{
  "video_id": "{os.path.basename(video_path)}",
  "video_duration_seconds": {duration:.2f},
  "video_summary": "short factual summary",
  "events": [
    {{
      "event_id": "EVT_001",
      "start_time": "00:00",
      "end_time": "00:00",
      "behavior": ["product_dragged"],
      "risk_level": "HIGH",
      "risk_score": 85,
      "evidence": "What is visibly happening",
      "potential_consequence": ["product_damage"],
      "recommended_action": "Corrective action",
      "confidence": 0.95,
      "status": "potential_risk"
    }}
  ]
}}

Constraints:
- risk_level: LOW, MEDIUM, HIGH, CRITICAL
- risk_score: 0-100
- confidence: 0-1
- status: observed_behaviour, potential_risk, confirmed_damage
- behavior must contain only predefined labels
- No Markdown
- No text outside JSON
"""


def _validate_events(events_data: dict, duration: float) -> None:
    """Raises AssertionError on any validation failure -- same checks as the notebook."""
    for event in events_data.get("events", []):
        required_fields = [
            "event_id", "start_time", "end_time", "behavior",
            "risk_level", "risk_score", "evidence",
            "potential_consequence", "recommended_action",
            "confidence", "status",
        ]
        for field in required_fields:
            assert field in event, f"{event.get('event_id', 'UNKNOWN')}: missing '{field}'"

        assert all(b in BEHAVIORS for b in event["behavior"]), f"Unknown behaviour in {event['event_id']}"
        assert event["risk_level"] in VALID_RISK
        assert 0 <= float(event["risk_score"]) <= 100
        assert 0 <= float(event["confidence"]) <= 1
        assert event["status"] in VALID_STATUS

        start = timestamp_to_seconds(event["start_time"])
        end = timestamp_to_seconds(event["end_time"])
        assert 0 <= start <= duration, f"{event['event_id']}: start timestamp outside video"
        assert 0 <= end <= duration, f"{event['event_id']}: end timestamp outside video"
        assert end >= start, f"{event['event_id']}: end_time before start_time"


def _attach_handling_rules(events_data: dict) -> dict:
    for event in events_data.get("events", []):
        event["handling_rules"] = []
        for behavior in event.get("behavior", []):
            if behavior in HANDLING_RULES:
                rule_id, rule_text = HANDLING_RULES[behavior]
                event["handling_rules"].append({"rule_id": rule_id, "rule": rule_text})
    return events_data


def _upload_once_and_wait(client: genai.Client, video_path: str):
    """Upload the video and poll until its state is ACTIVE. Raises
    RuntimeError if Gemini reports FAILED, the wait times out, or the Files
    API status endpoint keeps erroring."""
    video_file = client.files.upload(file=video_path)
    deadline = time.monotonic() + _video_processing_timeout_sec()
    transient_errors = 0
    while not video_file.state or video_file.state.name != "ACTIVE":
        if video_file.state and video_file.state.name == "FAILED":
            raise RuntimeError("Gemini failed to process the uploaded video.")
        if time.monotonic() > deadline:
            raise RuntimeError(
                f"Gemini video processing did not reach ACTIVE within "
                f"{_video_processing_timeout_sec():.0f}s "
                f"(last state: {getattr(video_file.state, 'name', None)})."
            )
        time.sleep(5)
        try:
            video_file = client.files.get(name=video_file.name)
        except errors.ServerError as exc:
            # The Files API status endpoint intermittently 500s ("Failed to
            # convert server response to JSON") independent of the actual
            # file state. Tolerate a few before giving up.
            transient_errors += 1
            if transient_errors > _MAX_TRANSIENT_POLL_ERRORS:
                raise RuntimeError(
                    f"Gemini Files API kept failing while polling video status "
                    f"({transient_errors} server errors): {exc}"
                ) from exc
    return video_file


def _upload_and_wait_active(client: genai.Client, video_path: str):
    """As _upload_once_and_wait, but retries the whole upload once if Gemini
    reports the file FAILED -- observed to be intermittent for the same clip
    (one attempt FAILED, the next ACTIVE, minutes apart)."""
    try:
        return _upload_once_and_wait(client, video_path)
    except RuntimeError as exc:
        if "failed to process" not in str(exc).lower():
            raise
        time.sleep(3)
        return _upload_once_and_wait(client, video_path)


def analyze_video(video_path: str) -> dict:
    """
    Uploads a video to Gemini, runs whole-video behavior analysis, validates
    the response, attaches handling rules, and returns the event log.

    Returns the same shape as warehouse_event_log.json in the original notebook:
        {
          "video_id": str,
          "video_duration_seconds": float,
          "video_summary": str,
          "events": [ {event_id, start_time, end_time, behavior, risk_level,
                       risk_score, evidence, potential_consequence,
                       recommended_action, confidence, status, handling_rules}, ... ]
        }

    Raises RuntimeError if the Gemini call fails or returns unusable output,
    and AssertionError if the response fails schema validation. Callers should
    catch both and fall back to kinematics-only results (see
    ml/behavior/fusion.py) rather than let the whole job fail.
    """
    client = _get_client()
    duration = _get_video_duration(video_path)

    video_file = _upload_and_wait_active(client, video_path)
    prompt = _build_prompt(video_path, duration)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[video_file, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            http_options=types.HttpOptions(retry_options=_retry_options()),
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    raw_output = response.text.strip()
    raw_output = re.sub(r"^```json\s*", "", raw_output, flags=re.IGNORECASE)
    raw_output = re.sub(r"^```\s*", "", raw_output)
    raw_output = re.sub(r"\s*```$", "", raw_output)

    events_data = json.loads(raw_output)  # raises json.JSONDecodeError on bad output
    _validate_events(events_data, duration)  # raises AssertionError on schema violation
    events_data = _attach_handling_rules(events_data)

    return events_data
