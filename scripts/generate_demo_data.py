#!/usr/bin/env python3
"""Exports a static JSON snapshot of the current backend state — dashboard
summary, full event list, active alerts — for the live demo's fallback path
(if the venue's WiFi/laptop dies, show this frozen file instead of the live
API).

This does NOT seed anything; run scripts/seed_database.py first so there's
real data to snapshot.

Usage:
  python scripts/generate_demo_data.py [--output PATH]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.database.database import SessionLocal  # noqa: E402
from app.services import alert_service, dashboard_service, event_service  # noqa: E402


def build_snapshot(db) -> dict:
    events = event_service.list_events(db, limit=1000)
    return {
        "dashboard_summary": dashboard_service.get_summary(db).model_dump(),
        "training_gaps": dashboard_service.get_training_gaps(db).model_dump()["items"],
        "events": [event_service.to_event_read_dict(e) for e in events],
        "alerts": [
            {"id": a.id, "event_id": a.event_id, "status": a.status, "created_at": a.created_at}
            for a in alert_service.list_alerts(db)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "demo_snapshot.json")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        snapshot = build_snapshot(db)
    finally:
        db.close()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, indent=2, default=str))
    print(f"Wrote demo snapshot ({len(snapshot['events'])} events) to {args.output}")


if __name__ == "__main__":
    main()
