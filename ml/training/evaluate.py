from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent
DATASET_YAML = BASE_DIR / "dataset.yaml"
DEFAULT_WEIGHTS = BASE_DIR.parent.parent / "models" / "fragility_finetune" / "weights" / "best.pt"

def evaluate(weights_path, data_yaml=None):
    model = YOLO(weights_path)
    metrics = model.val(data=str(data_yaml or DATASET_YAML))
    print(f"mAP50: {metrics.box.map50}")
    print(f"mAP50-95: {metrics.box.map}")
    return metrics

if __name__ == "__main__":
    evaluate(str(DEFAULT_WEIGHTS))