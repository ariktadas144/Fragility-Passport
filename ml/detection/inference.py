from detector import Detector
import sys

if __name__ == "__main__":
    weights = sys.argv[1] if len(sys.argv) > 1 else "yolov8n.pt"
    source = sys.argv[2] if len(sys.argv) > 2 else "../../data/frames"

    det = Detector(weights_path=weights)
    results = det.predict(source)
    print(f"Ran inference on {source} using {weights}")