"""Unit tests for the risk engine: score blending and contract-violation
detection, isolated from the database and HTTP layer entirely — these
construct model/schema objects directly in Python."""
from app.models.behavior import Behavior
from app.models.fragility_passport import FragilityPassport
from app.models.product import Product
from app.schemas.detection import DetectionIn
from app.services import risk_service


def _detection(**overrides) -> DetectionIn:
    defaults = dict(start_time="00:05", end_time="00:10", behavior=["product_dragged"], confidence=0.9)
    defaults.update(overrides)
    return DetectionIn(**defaults)


def test_determine_risk_level_thresholds():
    assert risk_service.determine_risk_level(0) == "LOW"
    assert risk_service.determine_risk_level(39.9) == "LOW"
    assert risk_service.determine_risk_level(40) == "MEDIUM"
    assert risk_service.determine_risk_level(64.9) == "MEDIUM"
    assert risk_service.determine_risk_level(65) == "HIGH"
    assert risk_service.determine_risk_level(85) == "CRITICAL"
    assert risk_service.determine_risk_level(100) == "CRITICAL"


def test_no_product_means_no_violation_and_no_exposure_estimate():
    detection = _detection(risk_score=90, confidence=0.95)
    behaviors = [Behavior(code="product_dragged", label="Dragging", category="kinetic", default_severity=3)]
    assessment = risk_service.calibrate_risk(detection, behaviors, passport=None, product=None)
    assert assessment.contract_clause_violated is None
    assert assessment.estimated_exposure_inr is None


def test_contract_violation_bumps_score_and_names_the_sku():
    detection = _detection(behavior=["product_dragged"], confidence=0.9)
    behaviors = [Behavior(code="product_dragged", label="Dragging", category="kinetic", default_severity=3)]
    product = Product(id=1, sku="ABC-123", name="KD Panel", category="kd-panel-furniture", declared_value_inr=8000)
    passport = FragilityPassport(
        product_id=1,
        max_tilt_deg=40,
        max_drop_height_cm=5,
        required_orientation="UPRIGHT",
        max_stack_weight_kg=10,
        drag_allowed=False,
        throw_allowed=False,
    )

    without_passport = risk_service.calibrate_risk(detection, behaviors, passport=None, product=None)
    with_passport = risk_service.calibrate_risk(detection, behaviors, passport=passport, product=product)

    assert with_passport.risk_score > without_passport.risk_score
    assert with_passport.contract_clause_violated is not None
    assert "ABC-123" in with_passport.contract_clause_violated
    assert "dragging" in with_passport.contract_clause_violated.lower()
    assert with_passport.estimated_exposure_inr is not None
    assert with_passport.estimated_exposure_inr > 0


def test_allowed_behavior_does_not_violate_contract():
    # Pallets are meant to be dragged (pallet-jack handling) — dragging a
    # pallet shouldn't trigger a violation the way dragging a KD panel does.
    detection = _detection(behavior=["product_dragged"], confidence=0.9)
    behaviors = [Behavior(code="product_dragged", label="Dragging", category="kinetic", default_severity=3)]
    product = Product(id=2, sku="PALLET-001", name="Wooden Pallet", category="pallet", declared_value_inr=2500)
    passport = FragilityPassport(
        product_id=2,
        max_tilt_deg=90,
        max_drop_height_cm=50,
        required_orientation="ANY",
        max_stack_weight_kg=500,
        drag_allowed=True,
        throw_allowed=False,
    )

    assessment = risk_service.calibrate_risk(detection, behaviors, passport=passport, product=product)
    assert assessment.contract_clause_violated is None


def test_missing_ml_score_falls_back_to_behavior_severity():
    detection = _detection(risk_score=None, behavior=["product_thrown"], confidence=0.8)
    behaviors = [Behavior(code="product_thrown", label="Throwing", category="kinetic", default_severity=5)]
    assessment = risk_service.calibrate_risk(detection, behaviors, passport=None, product=None)
    # severity 5 -> the fallback ml_score is 100, should land in HIGH/CRITICAL
    assert assessment.risk_level in ("HIGH", "CRITICAL")
