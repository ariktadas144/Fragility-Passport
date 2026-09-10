from ultralytics import YOLO

class Tracker:
    def __init__(self, weights_path="yolov8n.pt"):
        self.model = YOLO(weights_path)

    def track_video(self, video_path):
        """Uses Ultralytics built-in ByteTrack integration."""
        results = self.model.track(source=video_path, tracker="bytetrack.yaml", save=True, persist=True)
        return results