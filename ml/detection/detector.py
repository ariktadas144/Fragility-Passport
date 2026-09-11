from ultralytics import YOLO

class Detector:
    def __init__(self, weights_path="yolov8n.pt", conf=0.25):
        self.model = YOLO(weights_path)
        self.conf = conf

    def predict(self, source):
        """source can be an image path, folder, or video path."""
        results = self.model.predict(source=source, conf=self.conf, save=True)
        return results

    def predict_frame(self, frame):
        """Run detection on a single numpy frame (from cv2)."""
        results = self.model.predict(source=frame, conf=self.conf, verbose=False)
        return results[0]