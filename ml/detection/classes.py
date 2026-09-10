CLASSES = ["carton", "pallet", "kd_panel", "mattress"]

def class_id_to_name(class_id):
    return CLASSES[class_id] if 0 <= class_id < len(CLASSES) else "unknown"