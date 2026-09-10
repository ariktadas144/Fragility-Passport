"""
Cross-validation fusion: combines two independent signals into one event log.

  1. Kinematics (ml/behavior/kinetic.py) -- fast, free, physics-based motion
     detection from YOLO+ByteTrack tracking. Catches sudden velocity/drop
     events. Blind to static risks (e.g. heavy-on-light stacking) because
     nothing moves fast in that case -- confirmed by testing against real
     pilot footage (clips 2 and 5).

  2. Gemini whole-video analysis (ml/vlm/gemini_analysis.py) -- semantic
     understanding of behavior from the actual video content. Catches both
     motion and static risks, but has no independent physics signal to
     cross-check its own confidence.

Neither signal is trusted alone. Where both flag the same time window,
that's a high-confidence "confirmed" event -- two independent modalities
agree. Where only one flags it, it's still reported, but tagged so the
dashboard/assistant can show the difference (this maps directly onto the
brief's Observed -> Potential Risk -> Confirmed Damage ladder).
"""

from typing import List, Dict

# How much a kinematics motion-flag window and a Gemini event window need to
# overlap (in seconds) to be considered "the same event." Loose on purpose --
# the two pipelines measure time differently (frame-based vs. Gemini's own
# temporal understanding) and won't line up to the millisecond.
OVERLAP_TOLERANCE_SEC = 3.0


def _windows_overlap(a_start: float, a_end: float, b_start: float, b_end: float, tolerance: float) -> bool:
    return (a_start - tolerance) <= b_end and (b_start - tolerance) <= a_end


def fuse_events(kinematic_events: List[dict], gemini_events: List[dict]) -> List[Dict]:
    """
    kinematic_events: from backend/app/api/videos.py's per-track risk
        classification, each with start_time/end_time (seconds, floats)
    gemini_events: from ml/vlm/gemini_analysis.analyze_video()'s "events"
        list, each with start_time/end_time (Gemini's "MM:SS" strings --
        convert with ml.vlm.gemini_analysis.timestamp_to_seconds before
        calling this function)

    Returns a unified list, each item tagged with "source":
        "confirmed_both"     -- kinematics AND Gemini both flagged this window
        "vlm_only"           -- only Gemini flagged it (e.g. static/stacking risk)
        "kinematics_only"    -- only motion tracking flagged it (Gemini may have
                                 missed it, or it's a false positive worth
                                 lower confidence -- surface it, don't hide it)
    """
    fused = []
    matched_gemini_indices = set()

    for k_event in kinematic_events:
        k_start, k_end = k_event["start_time"], k_event["end_time"]
        matched = False

        for i, g_event in enumerate(gemini_events):
            g_start, g_end = g_event["_start_sec"], g_event["_end_sec"]
            if _windows_overlap(k_start, k_end, g_start, g_end, OVERLAP_TOLERANCE_SEC):
                fused.append({
                    "source": "confirmed_both",
                    "start_time": min(k_start, g_start),
                    "end_time": max(k_end, g_end),
                    "kinematic_signal": k_event,
                    "vlm_signal": g_event,
                    "risk_level": g_event.get("risk_level", "MEDIUM"),  # trust VLM's semantic risk level
                })
                matched_gemini_indices.add(i)
                matched = True
                break

        if not matched:
            fused.append({
                "source": "kinematics_only",
                "start_time": k_start,
                "end_time": k_end,
                "kinematic_signal": k_event,
                "vlm_signal": None,
                "risk_level": k_event.get("risk_level", "medium").upper(),
            })

    for i, g_event in enumerate(gemini_events):
        if i not in matched_gemini_indices:
            fused.append({
                "source": "vlm_only",
                "start_time": g_event["_start_sec"],
                "end_time": g_event["_end_sec"],
                "kinematic_signal": None,
                "vlm_signal": g_event,
                "risk_level": g_event.get("risk_level", "MEDIUM"),
            })

    fused.sort(key=lambda e: e["start_time"])
    return fused


def prepare_gemini_events_for_fusion(gemini_events: List[dict]) -> List[dict]:
    """Adds _start_sec/_end_sec (float seconds) to each Gemini event, computed
    from its MM:SS timestamp strings, without mutating the original fields --
    keeps the raw Gemini output intact for display/audit while making it
    usable for time-window comparison."""
    from ml.vlm.gemini_analysis import timestamp_to_seconds
    prepared = []
    for e in gemini_events:
        e = dict(e)
        e["_start_sec"] = timestamp_to_seconds(e["start_time"])
        e["_end_sec"] = timestamp_to_seconds(e["end_time"])
        prepared.append(e)
    return prepared
