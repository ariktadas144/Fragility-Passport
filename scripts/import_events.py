#!/usr/bin/env python3
"""Imports a VLM-notebook-style event log (warehouse_event_log.json) — or
any JSON file matching the same shape — into the backend through the real
ingestion pipeline (risk scoring + alert creation included).

The notebook's own field names (event_id, start_time, end_time, behavior,
risk_level, risk_score, confidence, evidence, potential_consequence,
recommended_action, status) match schemas.DetectionIn 1:1, so a file it
produces needs zero transformation here beyond attaching a dock/product.

Usage:
  python scripts/import_events.py path/to/warehouse_event_log.json \\
      [--dock DOCK] [--source-clip-ref NAME] [--product-sku SKU]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from pydantic import ValidationError  # noqa: E402

from app.database.database import SessionLocal, init_db  # noqa: E402
from app.schemas.detection import DetectionIn  # noqa: E402
from app.services import event_service  # noqa: E402


def _load_event_dicts(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "events" in data:
        return data["events"]
    raise ValueError(f"{path} doesn't look like an event log (expected a list, or a dict with an 'events' key)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("event_log", type=Path, help="Path to a warehouse_event_log.json-shaped file")
    parser.add_argument("--dock", default=None, help="Dock to attach every imported event to")
    parser.add_argument("--source-clip-ref", default=None, help="Video filename/id, if known")
    parser.add_argument("--product-sku", default=None, help="Product SKU, if every event in this file is the same product")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    imported, skipped = 0, 0
    try:
        for raw_event in _load_event_dicts(args.event_log):
            raw_event = dict(raw_event)
            raw_event.setdefault("dock", args.dock)
            raw_event.setdefault("source_clip_ref", args.source_clip_ref)
            raw_event.setdefault("product_sku", args.product_sku)
            try:
                payload = DetectionIn(**raw_event)
            except ValidationError as exc:
                print(f"Skipping invalid event {raw_event.get('event_id', '?')}: {exc}", file=sys.stderr)
                skipped += 1
                continue
            event_service.ingest_detection(db, payload)
            imported += 1
    finally:
        db.close()

    print(f"Imported {imported} event(s), skipped {skipped} invalid one(s).")


if __name__ == "__main__":
    main()
