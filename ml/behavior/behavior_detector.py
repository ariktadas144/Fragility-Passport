from kinetic import calc_velocity, calc_drop_height, calc_tilt_angle
from orientation import is_horizontal_when_should_be_vertical

def classify_event(trajectory, contract=None):
    """trajectory: list of (frame_idx, box). contract: fragility contract dict."""
    if len(trajectory) < 2:
        return None

    events = []
    for i in range(1, len(trajectory)):
        f0, box0 = trajectory[i-1]
        f1, box1 = trajectory[i]
        dt = f1 - f0
        vel = calc_velocity(box0, box1, dt)
        drop = calc_drop_height(box0[1], box1[1])
        tilt = calc_tilt_angle(box1)

        risk = "Low"
        reason = []
        if drop > (contract.get("max_drop_height", 50) if contract else 50):
            risk = "High"
            reason.append(f"drop height {drop:.1f} exceeded limit")
        if is_horizontal_when_should_be_vertical(tilt):
            risk = "Critical"
            reason.append(f"tilt {tilt:.1f} deg, should be upright")

        events.append({"frame": f1, "velocity": vel, "drop": drop, "tilt": tilt, "risk": risk, "reason": reason})
    return events