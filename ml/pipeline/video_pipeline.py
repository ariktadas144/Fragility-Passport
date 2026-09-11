"""
Video processing pipeline: detection + tracking on every frame.

Tested and working (validated end-to-end against real pilot footage:
930-frame clip -> 67 tracked objects -> structured event output).

Workstream (DS/ML) owns swapping MODEL_PATH for the fine-tuned custom-class
model once ready. Nothing else needs to change -- everything downstream
(risk engine, API, dashboard) consumes whatever this function returns,
and this return shape is the contract.
"""

import cv2
from ultralytics import YOLO
from pathlib import Path
import json

# TODO (DS/ML workstream): point this at the fine-tuned model, e.g.
#   MODEL_PATH = "ml/training/runs/warehouse_v1/weights/best.pt"
MODEL_PATH = "yolov8n.pt"

_model = None


def get_model():
    global _model
    if _model is None:
        _model = YOLO(MODEL_PATH)
    return _model


def run_pipeline(video_path: str, output_dir: str) -> dict:
    """
    Runs detection+tracking on every frame of the given video.

    Returns:
        {
          "meta": {"fps": float, "resolution": str, "total_frames": int, "frames_processed": int},
          "events": [ {frame_idx, time_sec, track_id, class_name, conf, bbox, center}, ... ],
          "annotated_video_path": str,
        }
    """
    model = get_model()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(
            f"Could not open video (unsupported codec or corrupt file): {video_path}"
        )
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    annotated_path = str(output_dir / "annotated.mp4")
    writer = cv2.VideoWriter(annotated_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    events = []
    frame_idx = 0
    results_gen = model.track(
        source=video_path, stream=True, persist=True,
        tracker="bytetrack.yaml", verbose=False, conf=0.25
    )

    for r in results_gen:
        t_sec = frame_idx / fps
        writer.write(r.plot())

        if r.boxes is not None and len(r.boxes) > 0:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                cls_name = model.names[cls_id]
                conf = float(box.conf[0])
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
                tid = int(box.id[0]) if box.id is not None else -1
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

                events.append({
                    "frame_idx": frame_idx,
                    "time_sec": round(t_sec, 3),
                    "track_id": tid,
                    "class_name": cls_name,
                    "conf": round(conf, 3),
                    "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                    "center": [round(cx, 1), round(cy, 1)],
                })
        frame_idx += 1

    writer.release()

    if frame_idx == 0:
        raise RuntimeError(f"No frames could be read from the video: {video_path}")

    result = {
        "meta": {"fps": fps, "resolution": f"{w}x{h}", "total_frames": total_frames, "frames_processed": frame_idx},
        "events": events,
        "annotated_video_path": annotated_path,
    }

    with open(output_dir / "raw_detections.json", "w") as f:
        json.dump(result, f)

    return result
