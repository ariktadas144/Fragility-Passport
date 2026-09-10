import csv
import os
import random
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(BASE_DIR, "..", "..", "data", "frames")
REPORT_CSV = os.path.join(BASE_DIR, "..", "..", "data", "overlay_screen_report.csv")
DATASET_DIR = os.path.join(BASE_DIR, "..", "..", "data", "dataset")

VAL_FRACTION = 0.15
SEED = 42

def main():
    with open(REPORT_CSV, newline="") as f:
        rows = list(csv.DictReader(f))

    clean_by_video = {}
    for row in rows:
        if row["flagged"] == "False":
            clean_by_video.setdefault(row["video"], []).append(row["frame"])

    rng = random.Random(SEED)
    train_files, val_files = [], []
    for video, frames in clean_by_video.items():
        frames = sorted(frames)
        rng.shuffle(frames)
        n_val = max(1, round(len(frames) * VAL_FRACTION)) if len(frames) > 1 else 0
        val_files.extend(frames[:n_val])
        train_files.extend(frames[n_val:])

    for split, files in [("train", train_files), ("val", val_files)]:
        img_dir = os.path.join(DATASET_DIR, "images", split)
        lbl_dir = os.path.join(DATASET_DIR, "labels", split)
        os.makedirs(img_dir, exist_ok=True)
        os.makedirs(lbl_dir, exist_ok=True)
        for fname in files:
            shutil.copy2(os.path.join(FRAMES_DIR, fname), os.path.join(img_dir, fname))

    print(f"Clean frames found: {len(train_files) + len(val_files)} (train={len(train_files)}, val={len(val_files)})")
    print("\nPer video (clean frames used):")
    for video, frames in clean_by_video.items():
        print(f"  {video}: {len(frames)}")
    print(f"\nImages copied to: {os.path.join(DATASET_DIR, 'images')}")
    print(f"Now label each image and save YOLO-format .txt files into: {os.path.join(DATASET_DIR, 'labels')}")
    print("(one .txt per image, same filename, class indices per ml/training/dataset.yaml: 0=carton 1=pallet 2=kd_panel 3=mattress)")

if __name__ == "__main__":
    main()
