def is_upright(tilt_angle, threshold=15):
    return abs(90 - abs(tilt_angle)) < threshold

def is_horizontal_when_should_be_vertical(tilt_angle, required_orientation="vertical"):
    if required_orientation == "vertical" and abs(tilt_angle) < 30:
        return True
    return False