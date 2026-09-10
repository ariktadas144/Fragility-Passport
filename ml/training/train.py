from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent
DATASET_YAML = BASE_DIR / "dataset.yaml"
MODELS_DIR = BASE_DIR.parent.parent / "models"

def main():
    model = YOLO("yolov8n.pt")
    model.train(data=str(DATASET_YAML), epochs=25, imgsz=640, batch=8, project=str(MODELS_DIR), name="fragility_finetune")

if __name__ == "__main__":
    main()