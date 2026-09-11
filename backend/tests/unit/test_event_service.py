"""Tests for the event ingestion pipeline: the single front door every
detection goes through (event_service.ingest_detection)."""
import pytest

from app.core.exceptions import ValidationFailedError
from app.models.behavior import Behavior
from app.models.fragility_passport import FragilityPassport
from app.models.product import Product
from app.schemas.detection import DetectionIn
from app.services import event_service


def _seed_dragging_behavior(db_session):
    db_session.add(Behavior(code="product_dragged", label="Dragging", category="kinetic", default_severity=3))
    db_session.commit()


def _seed_kd_panel_with_passport(db_session) -> Product:
    product = Product(sku="ABC-123", name="KD Panel Cupboard", category="kd-panel-furniture", declared_value_inr=8000)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    db_session.add(
        FragilityPassport(
            product_id=product.id,
            max_tilt_deg=40,
            max_drop_height_cm=5,
            required_orientation="UPRIGHT",
            max_stack_weight_kg=10,
            drag_allowed=False,
            throw_allowed=False,
        )
    )
    db_session.commit()
    return product


def test_ingest_detection_creates_event_and_links_behavior(db_session):
    _seed_dragging_behavior(db_session)
    payload = DetectionIn(
        event_id="EVT_TEST_01", start_time="00:05", end_time="00:10",
        behavior=["product_dragged"], confidence=0.9, dock="07",
    )
    event = event_service.ingest_detection(db_session, payload)

    assert event.public_id == "EVT_TEST_01"
    assert event.dock == "07"
    assert event.start_time_seconds == 5.0
    assert len(event.behavior_links) == 1
    assert event.behavior_links[0].behavior.code == "product_dragged"


def test_ingest_detection_resolves_product_and_applies_passport(db_session):
    _seed_dragging_behavior(db_session)
    _seed_kd_panel_with_passport(db_session)
    payload = DetectionIn(
        event_id="EVT_TEST_02", start_time="00:05", end_time="00:10",
        behavior=["product_dragged"], confidence=0.9, product_sku="ABC-123",
    )
    event = event_service.ingest_detection(db_session, payload)

    assert event.product_id is not None
    assert event.contract_clause_violated is not None
    assert "ABC-123" in event.contract_clause_violated
    assert event.risk_level in ("HIGH", "CRITICAL")


def test_ingest_detection_rejects_end_before_start(db_session):
    _seed_dragging_behavior(db_session)
    payload = DetectionIn(
        event_id="EVT_TEST_03", start_time="00:10", end_time="00:05",
        behavior=["product_dragged"], confidence=0.9,
    )
    with pytest.raises(ValidationFailedError):
        event_service.ingest_detection(db_session, payload)


def test_duplicate_public_id_gets_a_fresh_generated_one(db_session):
    _seed_dragging_behavior(db_session)
    shared_fields = dict(start_time="00:05", end_time="00:10", behavior=["product_dragged"], confidence=0.9)

    first = event_service.ingest_detection(db_session, DetectionIn(event_id="EVT_DUP", **shared_fields))
    second = event_service.ingest_detection(db_session, DetectionIn(event_id="EVT_DUP", **shared_fields))

    assert first.public_id == "EVT_DUP"
    assert second.public_id != "EVT_DUP"  # collision handled by generating a new id, not crashing
    assert second.public_id.startswith("EVT_")


def test_high_risk_event_creates_an_alert(db_session):
    _seed_dragging_behavior(db_session)
    _seed_kd_panel_with_passport(db_session)
    payload = DetectionIn(
        event_id="EVT_TEST_04", start_time="00:05", end_time="00:10",
        behavior=["product_dragged"], confidence=0.9, product_sku="ABC-123",
    )
    event = event_service.ingest_detection(db_session, payload)
    assert len(event.alerts) == 1
    assert event.alerts[0].status == "ACTIVE"
