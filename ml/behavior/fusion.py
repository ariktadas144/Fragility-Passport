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
    kinematic_events: from ml/pipeline/orchestrator.py's per-track risk
        classification, each with start_time/end_time (seconds, floats)
    gemini_events: from ml/vlm/gemini_analysis.analyze_video()'s "events"
        list, each with start_time/end_time (Gemini's "MM:SS" strings --
        convert with ml.vlm.gemini_analysis.timestamp_to_seconds before
        calling this function)

    The output has ONE entry per real-world event, tagged with "source":
        "confirmed_both"     -- a Gemini event that one or more kinematic
                                 windows overlap. All the overlapping
                                 kinematic signals are attached
                                 (`kinematic_signals`); `kinematic_signal`
                                 holds the first for backwards compatibility.
        "vlm_only"           -- a Gemini event no kinematic window overlaps
                                 (e.g. a static/stacking risk).
        "kinematics_only"    -- a kinematic window no Gemini event overlaps
                                 (Gemini may have missed it, or it's a false
                                 positive worth lower confidence -- surface
                                 it, don't hide it).

    Anchoring on the Gemini events (rather than iterating kinematic events and
    emitting one confirmed_both per match) is what stops a single semantic
    event from being reported N times when N tracked objects move through its
    time window.
    """
    fused: List[Dict] = []
    matched_kinematic_ids = set()

    for g_event in gemini_events:
        g_start, g_end = g_event["_start_sec"], g_event["_end_sec"]

        overlapping = []
        for i, k in enumerate(kinematic_events):
            if i in matched_kinematic_ids:
                continue
            if _windows_overlap(k["start_time"], k["end_time"], g_start, g_end, OVERLAP_TOLERANCE_SEC):
                overlapping.append(k)
                matched_kinematic_ids.add(i)

        if overlapping:
            fused.append({
                "source": "confirmed_both",
                "start_time": min(g_start, min(k["start_time"] for k in overlapping)),
                "end_time": max(g_end, max(k["end_time"] for k in overlapping)),
                "kinematic_signal": overlapping[0],
                "kinematic_signals": overlapping,
                "vlm_signal": g_event,
                "risk_level": g_event.get("risk_level", "MEDIUM"),  # trust VLM's semantic risk level
            })
        else:
            fused.append({
                "source": "vlm_only",
                "start_time": g_start,
                "end_time": g_end,
                "kinematic_signal": None,
                "kinematic_signals": [],
                "vlm_signal": g_event,
                "risk_level": g_event.get("risk_level", "MEDIUM"),
            })

    for i, k_event in enumerate(kinematic_events):
        if i in matched_kinematic_ids:
            continue
        fused.append({
            "source": "kinematics_only",
            "start_time": k_event["start_time"],
            "end_time": k_event["end_time"],
            "kinematic_signal": k_event,
            "kinematic_signals": [k_event],
            "vlm_signal": None,
            "risk_level": k_event.get("risk_level", "medium").upper(),
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
