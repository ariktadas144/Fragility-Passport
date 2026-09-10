from spatial import boxes_overlap

def is_heavy_on_light(box_top, box_bottom, weight_top, weight_bottom):
    """box_top is physically above box_bottom in the frame."""
    if boxes_overlap(box_top, box_bottom) and weight_top > weight_bottom:
        return True
    return False