import math

def calc_velocity(box1, box2, dt):
    cx1, cy1 = (box1[0]+box1[2])/2, (box1[1]+box1[3])/2
    cx2, cy2 = (box2[0]+box2[2])/2, (box2[1]+box2[3])/2
    dist = ((cx2-cx1)**2 + (cy2-cy1)**2) ** 0.5
    return dist / dt if dt > 0 else 0

def calc_drop_height(y_start, y_end):
    """Positive when the box moves downward (y increases) between frames; upward motion (lifting) returns 0."""
    return max(y_end - y_start, 0)

def calc_tilt_angle(box):
    w = box[2] - box[0]
    h = box[3] - box[1]
    return math.degrees(math.atan2(h, w))