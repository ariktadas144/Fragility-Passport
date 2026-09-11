"""Loads the JSON files in data/seed/ into the database. Used by
scripts/seed_database.py. Every loader is idempotent — safe to run
repeatedly without creating duplicate rows, since a hackathon demo often
needs "wipe and reseed" more than once.

The pilot events are inserted through the real event_service.ingest_detection()
pipeline (not raw INSERTs), so risk scoring, passport contract checks, and
alert creation all run for real on this seed data.
"""
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.behavior import Behavior
from app.models.event import Event
from app.models.fragility_passport import FragilityPassport
from app.models.product import Product
from app.models.video import Video
from app.schemas.detection import DetectionIn
from app.services import event_service


def seed_behaviors(db: Session, path: Path) -> int:
    entries = json.loads(path.read_text(encoding="utf-8"))
    created = 0
    for entry in entries:
        if db.query(Behavior).filter(Behavior.code == entry["code"]).first() is not None:
            continue
        db.add(
            Behavior(
                code=entry["code"],
                label=entry["label"],
                category=entry["category"],
                default_severity=entry["default_severity"],
            )
        )
        created += 1
    db.commit()
    return created


def seed_products(db: Session, path: Path) -> int:
    entries = json.loads(path.read_text(encoding="utf-8"))
    created = 0
    for entry in entries:
        if db.query(Product).filter(Product.sku == entry["sku"]).first() is not None:
            continue
        db.add(
            Product(
                sku=entry["sku"],
                name=entry["name"],
                category=entry["category"],
                declared_value_inr=entry.get("declared_value_inr", 0.0),
            )
        )
        created += 1
    db.commit()
    return created


def seed_passports(db: Session, path: Path) -> int:
    entries = json.loads(path.read_text(encoding="utf-8"))
    created = 0
    for entry in entries:
        product = db.query(Product).filter(Product.sku == entry["product_sku"]).first()
        if product is None:
            continue  # referenced product wasn't seeded; don't crash the whole run over it
        if db.query(FragilityPassport).filter(FragilityPassport.product_id == product.id).first() is not None:
            continue
        db.add(
            FragilityPassport(
                product_id=product.id,
                max_tilt_deg=entry["max_tilt_deg"],
                max_drop_height_cm=entry["max_drop_height_cm"],
                required_orientation=entry["required_orientation"],
                max_stack_weight_kg=entry["max_stack_weight_kg"],
                drag_allowed=entry["drag_allowed"],
                throw_allowed=entry["throw_allowed"],
                notes=entry.get("notes"),
            )
        )
        created += 1
    db.commit()
    return created


def seed_pilot_events(db: Session, path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    created = 0
    for clip in data["clips"]:
        video = db.query(Video).filter(Video.source_clip_ref == clip["filename"]).first()
        if video is None:
            video = Video(
                filename=clip["filename"],
                source_clip_ref=clip["filename"],
                dock=clip["dock"],
                status="processed",
            )
            db.add(video)
            db.commit()
            db.refresh(video)

        for event_entry in clip["events"]:
            if db.query(Event).filter(Event.public_id == event_entry["event_id"]).first() is not None:
                continue  # already seeded

            payload = DetectionIn(
                event_id=event_entry["event_id"],
                video_id=video.id,
                dock=clip["dock"],
                product_sku=event_entry.get("product_sku"),
                start_time=event_entry["start_time"],
                end_time=event_entry["end_time"],
                behavior=event_entry["behavior"],
                confidence=event_entry["confidence"],
                evidence=event_entry.get("evidence"),
                status=event_entry.get("status", "observed_behaviour"),
            )
            event_service.ingest_detection(db, payload)
            created += 1

    return created


def seed_all(db: Session, seed_dir: Path) -> dict[str, int]:
    return {
        "behaviors": seed_behaviors(db, seed_dir / "behaviors.json"),
        "products": seed_products(db, seed_dir / "products.json"),
        "fragility_passports": seed_passports(db, seed_dir / "fragility_passports.json"),
        "pilot_events": seed_pilot_events(db, seed_dir / "pilot_events.json"),
    }
