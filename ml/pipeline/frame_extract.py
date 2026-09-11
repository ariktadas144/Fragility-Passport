"""Frame extraction + per-frame detection (DS/ML workstream).

Was `ml/pipeline/video_pipeline.py` in the "Initial ML workstream" merge;
renamed here because Workstream 5's `video_pipeline.run_pipeline` (YOLO +
ByteTrack -> event stream) is the module the orchestrator / backend / upload
endpoint depend on. This dumps every Nth frame as a JPEG and runs the
staged `ml.detection.Detector` on it -- exploratory, not wired into the
live pipeline. Reconcile the two when the fine-tuned detector is ready.
"""

import cv2
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE, "..", "detection"))
from detector import Detector

FRAMES_OUT = os.path.join(BASE, "..", "..", "data", "frames")
RAW_VIDEOS = os.path.join(BASE, "..", "..", "data", "raw")

def extract_and_detect(video_path, det, out_dir=FRAMES_OUT, every_n=10):
    os.makedirs(out_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    name = os.path.splitext(os.path.basename(video_path))[0]
    i = 0
    saved = 0
    all_detections = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if i % every_n == 0:
            frame_path = os.path.join(out_dir, f"{name}_{i:04d}.jpg")
            cv2.imwrite(frame_path, frame)
            result = det.predict_frame(frame)
            all_detections.append({
                "frame": frame_path,
                "boxes": result.boxes.data.tolist() if result.boxes is not None else []
            })
            saved += 1
        i += 1

    cap.release()
    print(f"{video_path}: saved {saved} frames, ran detection on each")
    return all_detections

if __name__ == "__main__":
    det = Detector(weights_path="yolov8n.pt")  # loaded once, reused for all videos

    for vid in os.listdir(RAW_VIDEOS):
        if vid.lower().endswith((".mp4", ".mov", ".avi")):
            extract_and_detect(os.path.join(RAW_VIDEOS, vid), det)