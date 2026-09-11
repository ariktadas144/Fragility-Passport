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
