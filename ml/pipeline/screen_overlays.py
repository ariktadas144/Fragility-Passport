import csv
import os
import cv2
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(BASE_DIR, "..", "..", "data", "frames")
REPORT_OUT = os.path.join(BASE_DIR, "..", "..", "data", "overlay_screen_report.csv")
CONTACT_SHEET_DIR = os.path.join(BASE_DIR, "..", "..", "data", "overlay_review")

THUMB_W, THUMB_H = 220, 124
COLS = 6

MIN_BLOB_AREA = 1500  # contiguous saturated-red region size (px) needed to count as an annotation mark

def largest_red_blob_area(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # tight range: vivid, near-pure red (annotation color), not skin/rust/wood tones
    lower1, upper1 = np.array([0, 180, 140]), np.array([8, 255, 255])
    lower2, upper2 = np.array([172, 180, 140]), np.array([180, 255, 255])
    mask = cv2.inRange(hsv, lower1, upper1) | cv2.inRange(hsv, lower2, upper2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0
    return max(cv2.contourArea(c) for c in contours)

def make_contact_sheet(video_name, flagged_frames, out_path):
    thumbs = []
    for fname in flagged_frames:
        img = cv2.imread(os.path.join(FRAMES_DIR, fname))
        if img is None:
            continue
        thumb = cv2.resize(img, (THUMB_W, THUMB_H))
        frame_idx = fname.rsplit("_", 1)[1].split(".")[0]
        cv2.rectangle(thumb, (0, 0), (THUMB_W, 18), (0, 0, 0), -1)
        cv2.putText(thumb, frame_idx, (3, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1, cv2.LINE_AA)
        thumbs.append(thumb)

    if not thumbs:
        return
    rows_of_thumbs = [thumbs[i:i + COLS] for i in range(0, len(thumbs), COLS)]
    row_imgs = []
    for row in rows_of_thumbs:
        while len(row) < COLS:
            row.append(np.zeros((THUMB_H, THUMB_W, 3), np.uint8))
        row_imgs.append(np.hstack(row))
    sheet = np.vstack(row_imgs)
    cv2.imwrite(out_path, sheet)

def main():
    os.makedirs(CONTACT_SHEET_DIR, exist_ok=True)
    rows = []
    flagged_by_video = {}
    filenames = sorted(f for f in os.listdir(FRAMES_DIR) if f.lower().endswith(".jpg"))
    for fname in filenames:
        path = os.path.join(FRAMES_DIR, fname)
        img = cv2.imread(path)
        if img is None:
            continue
        area = largest_red_blob_area(img)
        flagged = area > MIN_BLOB_AREA
        video = fname.rsplit("_", 1)[0]
        rows.append({
            "video": video,
            "frame": fname,
            "max_red_blob_area": int(area),
            "flagged": flagged,
        })
        if flagged:
            flagged_by_video.setdefault(video, []).append(fname)

    for video, frames in flagged_by_video.items():
        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in video)
        out_path = os.path.join(CONTACT_SHEET_DIR, f"{safe_name}.jpg")
        make_contact_sheet(video, frames, out_path)

    with open(REPORT_OUT, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["video", "frame", "max_red_blob_area", "flagged"])
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    flagged = sum(1 for r in rows if r["flagged"])
    print(f"Scanned {total} frames, flagged {flagged} as likely containing a red annotation.")
    print(f"Report written to {REPORT_OUT}")
    print(f"Contact sheets written to {CONTACT_SHEET_DIR}")

    by_video = {}
    for r in rows:
        by_video.setdefault(r["video"], [0, 0])
        by_video[r["video"]][0] += 1
        if r["flagged"]:
            by_video[r["video"]][1] += 1
    print("\nPer video:")
    for video, (n, f) in by_video.items():
        print(f"  {video}: {f}/{n} flagged")

if __name__ == "__main__":
    main()
