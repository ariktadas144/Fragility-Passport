#!/usr/bin/env python3
"""Creates the database tables (if needed) and loads every file in
data/seed/ into it. Safe to run repeatedly.

Usage:
  python scripts/seed_database.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings  # noqa: E402
from app.database.database import SessionLocal, init_db  # noqa: E402
from app.database.seed import seed_all  # noqa: E402


def main() -> None:
    settings = get_settings()
    init_db()
    db = SessionLocal()
    try:
        counts = seed_all(db, settings.seed_data_dir)
    finally:
        db.close()

    print("Seed complete:")
    for name, count in counts.items():
        print(f"  {name}: {count} new row(s)")


if __name__ == "__main__":
    main()
