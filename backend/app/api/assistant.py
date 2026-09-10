"""
Conversational assistant endpoint -- grounded Q&A over a job's fused event log.
Real reasoning lives in ml/vlm/assistant.py (three-step routing: local lookup,
grounded refusal for unavailable data, Gemini only for genuine reasoning).
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException
import json

from ml.vlm.assistant import warehouse_assistant

router = APIRouter()

BASE_DIR = Path(__file__).parent.parent.parent.parent
RESULTS_DIR = BASE_DIR / "data" / "processed"


@router.post("/assistant/{job_id}/ask")
async def ask_assistant(job_id: str, payload: dict):
    question = payload.get("question", "")
    summary_path = RESULTS_DIR / job_id / "summary.json"
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail="Job not found or not yet processed")

    with open(summary_path) as f:
        summary = json.load(f)

    # warehouse_assistant expects the Gemini-shaped {"events": [...]} log.
    # Build that view from the fused events (VLM signal, when present, carries
    # the fields the assistant's local lookups expect -- event_id, behavior,
    # risk_level, etc.). Events with no VLM signal (kinematics_only) are
    # included with what we have so the assistant can still count/list them.
    events_for_assistant = []
    for e in summary.get("fused_events", []):
        if e.get("vlm_signal"):
            events_for_assistant.append(e["vlm_signal"])
        else:
            k = e["kinematic_signal"]
            events_for_assistant.append({
                "event_id": f"KIN_{k['track_id']}",
                "start_time": f"{int(e['start_time']) // 60:02d}:{e['start_time'] % 60:05.2f}",
                "end_time": f"{int(e['end_time']) // 60:02d}:{e['end_time'] % 60:05.2f}",
                "behavior": [k.get("behavior", "unknown")],
                "risk_level": e["risk_level"],
                "risk_score": 50,
                "evidence": k.get("explanation", ""),
                "potential_consequence": [],
                "recommended_action": "Review footage -- flagged by motion tracking only, not confirmed by video analysis.",
                "confidence": 0.5,
                "status": "observed_behaviour",
                "handling_rules": [],
            })

    data = {"events": events_for_assistant}
    answer = warehouse_assistant(question, data)
    return {"answer": answer}
