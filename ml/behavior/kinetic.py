"""
Kinetic risk module: velocity, drop height, and motion-based risk signals
computed from tracked object trajectories.

This is the "motion" half of the dual-detection architecture (the other
half being ml/behavior/spatial.py + stacking.py for static/configuration
risks like heavy-on-light stacking, which motion tracking alone cannot
catch -- confirmed by testing against real pilot footage).
"""

from typing import List


def compute_kinematics(events: List[dict], track_id: int) -> List[dict]:
    """
    For a given track ID, compute velocity and vertical displacement
    between consecutive frames. Feeds the risk engine / VLM reasoning layer.

    NOTE: events with track_id == -1 (untracked detections -- YOLO/ByteTrack
    couldn't assign a persistent ID, common on first appearance or heavy
    occlusion) should be filtered out BEFORE calling this function. Grouping
    them together produces nonsense kinematics between unrelated objects.
    """
    track_events = sorted(
        [e for e in events if e["track_id"] == track_id],
        key=lambda e: e["frame_idx"]
    )
    kinematics = []
    for i in range(1, len(track_events)):
        prev, cur = track_events[i - 1], track_events[i]
        dt = cur["time_sec"] - prev["time_sec"]
        if dt <= 0:
            continue
        dx = cur["center"][0] - prev["center"][0]
        dy = cur["center"][1] - prev["center"][1]
        velocity = ((dx ** 2 + dy ** 2) ** 0.5) / dt
        kinematics.append({
            "frame_idx": cur["frame_idx"],
            "time_sec": cur["time_sec"],
            "velocity_px_per_sec": round(velocity, 2),
            "vertical_drop_px": round(dy, 2),
        })
    return kinematics


def group_tracks(events: List[dict]) -> dict:
    """
    Groups raw pipeline events by track_id, excluding untracked (-1) detections.
    Returns {track_id: [events]} plus a count of excluded untracked detections.
    """
    from collections import defaultdict
    by_track = defaultdict(list)
    untracked_count = 0
    for e in events:
        if e["track_id"] == -1:
            untracked_count += 1
            continue
        by_track[e["track_id"]].append(e)
    return {"tracks": dict(by_track), "untracked_excluded": untracked_count}


# ---------------------------------------------------------------------------
# Frame-level kinetic primitives (DS/ML workstream, from the "Initial ML
# workstream" merge). These operate on raw [x1, y1, x2, y2] boxes rather than
# the pipeline's event stream. Not yet wired into run_pipeline / fusion --
# kept here so both APIs live in one module; reconcile with compute_kinematics
# above when the fine-tuned detector lands.
# ---------------------------------------------------------------------------

import math  # noqa: E402


def calc_velocity(box1, box2, dt):
    cx1, cy1 = (box1[0] + box1[2]) / 2, (box1[1] + box1[3]) / 2
    cx2, cy2 = (box2[0] + box2[2]) / 2, (box2[1] + box2[3]) / 2
    dist = ((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2) ** 0.5
    return dist / dt if dt > 0 else 0


def calc_drop_height(y_start, y_end):
    """Positive when the box moves downward (y increases) between frames; upward motion (lifting) returns 0."""
    return max(y_end - y_start, 0)


def calc_tilt_angle(box):
    w = box[2] - box[0]
    h = box[3] - box[1]
    return math.degrees(math.atan2(h, w))
