from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_WEIGHTS = BASE_DIR.parent.parent / "models" / "fragility_finetune" / "weights" / "best.pt"

def export_model(weights_path, format="onnx"):
    model = YOLO(weights_path)
    model.export(format=format)

if __name__ == "__main__":
    export_model(str(DEFAULT_WEIGHTS))