"""
VLM behavior classifier.

THIS IS A STUB with a working mock so the full pipeline is demoable
end-to-end today. VLM & AI Assistant workstream owns replacing
classify_event() with a real Gemini/Claude API call -- keep the same
return shape and nothing downstream (risk engine, API, dashboard) breaks.
"""

from typing import List, Dict


def classify_event(track_kinematics: List[dict], product_class: str = "unknown") -> Dict:
    """
    Input: kinematics samples for one tracked object (see ml/behavior/kinetic.py),
           plus an optional product class if the detector identified one.

    Output (KEEP THIS SHAPE STABLE):
        {
          "behavior": str,              # e.g. "dragging", "dropping", "normal"
          "risk_level": str,            # "low" | "medium" | "high" | "critical"
          "explanation": str,
          "contract_clause_violated": str or None,
        }

    TODO (VLM workstream): replace with a real API call. See ml/vlm/prompts.py
    for the suggested prompt template.
    """
    if not track_kinematics:
        return _normal_result()

    max_velocity = max(k["velocity_px_per_sec"] for k in track_kinematics)
    max_drop = max((k["vertical_drop_px"] for k in track_kinematics), default=0)
    duration = track_kinematics[-1]["time_sec"] - track_kinematics[0]["time_sec"]

    # Placeholder rule-based logic -- NOT the real system.
    if max_drop > 150 and max_velocity > 400:
        return {
            "behavior": "dropping",
            "risk_level": "high",
            "explanation": f"Object dropped ~{int(max_drop)}px vertically at high velocity ({int(max_velocity)}px/s) -- mock classification, replace with real VLM call.",
            "contract_clause_violated": "max_drop_height" if product_class != "unknown" else None,
        }
    if max_velocity > 300 and duration > 1.0:
        return {
            "behavior": "dragging",
            "risk_level": "medium",
            "explanation": f"Sustained horizontal motion at {int(max_velocity)}px/s over {duration:.1f}s -- mock classification, replace with real VLM call.",
            "contract_clause_violated": "no_drag_allowed" if product_class != "unknown" else None,
        }
    return _normal_result()


def _normal_result():
    return {
        "behavior": "normal",
        "risk_level": "low",
        "explanation": "No risk-indicating motion pattern detected -- mock classification.",
        "contract_clause_violated": None,
    }
