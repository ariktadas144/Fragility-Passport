"""The risk engine: turns a raw ML/VLM detection into a calibrated risk
score/level, and — where a Fragility Passport clause was actually broken —
a plain-language "SKU-class X violated clause Y" explanation (turning a
generic "risky!" into something specific and actionable). Full write-up in
docs/risk-engine.md.

estimated_exposure_inr is explicitly an industry-indicative estimate (a
product's declared value x a severity multiplier) — not an audited figure.
See the master plan's honesty checklist: these numbers show scale, they
aren't Godrej-specific guarantees.
"""
from dataclasses import dataclass, field

from app.core.constants import EXPOSURE_MULTIPLIER_BY_RISK_LEVEL, RISK_LEVEL_THRESHOLDS
from app.models.behavior import Behavior
from app.models.fragility_passport import FragilityPassport
from app.models.product import Product
from app.schemas.detection import DetectionIn


@dataclass
class RiskAssessment:
    risk_score: float
    risk_level: str
    contract_clause_violated: str | None
    estimated_exposure_inr: float | None
    violations: list[str] = field(default_factory=list)


def determine_risk_level(score: float) -> str:
    """RISK_LEVEL_THRESHOLDS is ordered LOW < MEDIUM < HIGH < CRITICAL; the
    level is the highest one the score clears."""
    level = "LOW"
    for candidate_level, threshold in RISK_LEVEL_THRESHOLDS.items():
        if score >= threshold:
            level = candidate_level
    return level


def _ml_reported_score(detection: DetectionIn, behaviors: list[Behavior]) -> float:
    if detection.risk_score is not None:
        return detection.risk_score
    # Upstream didn't send a score (e.g. a bare kinetic-module detection) —
    # fall back to the worst behavior's default severity (1-5 -> 20-100).
    if behaviors:
        return max(b.default_severity for b in behaviors) * 20
    return 40.0  # unknown severity: assume MEDIUM-ish rather than defaulting to 0


def check_contract_violations(
    detection: DetectionIn,
    behavior_codes: list[str],
    passport: FragilityPassport | None,
    product: Product | None,
) -> list[str]:
    """Plain-language clause-violation strings, e.g.
    "SKU-class ABC-123: tilt exceeded 40°. Contract requires upright transport only."
    Empty if there's no passport to check against, or nothing was violated.
    """
    if passport is None or product is None:
        return []

    violations: list[str] = []
    sku = product.sku

    if detection.tilt_deg is not None and detection.tilt_deg > passport.max_tilt_deg:
        violations.append(
            f"SKU-class {sku}: tilt exceeded {passport.max_tilt_deg:.0f}°. "
            f"Contract requires {passport.required_orientation.lower()} transport only."
        )

    if detection.drop_height_cm is not None and detection.drop_height_cm > passport.max_drop_height_cm:
        violations.append(
            f"SKU-class {sku}: drop height {detection.drop_height_cm:.0f}cm exceeded the "
            f"{passport.max_drop_height_cm:.0f}cm contract limit."
        )

    if "product_dragged" in behavior_codes and not passport.drag_allowed:
        violations.append(f"SKU-class {sku}: dragging detected. Contract prohibits dragging.")

    if "product_thrown" in behavior_codes and not passport.throw_allowed:
        violations.append(f"SKU-class {sku}: throwing detected. Contract prohibits throwing.")

    if "wrong_orientation" in behavior_codes and passport.required_orientation != "ANY":
        violations.append(
            f"SKU-class {sku}: incorrect orientation. Contract requires "
            f"{passport.required_orientation.lower()} orientation."
        )

    return violations


def estimate_exposure_inr(product: Product | None, risk_level: str) -> float | None:
    if product is None:
        return None
    multiplier = EXPOSURE_MULTIPLIER_BY_RISK_LEVEL.get(risk_level, 0.0)
    return round(product.declared_value_inr * multiplier, 2)


def calibrate_risk(
    detection: DetectionIn,
    behaviors: list[Behavior],
    passport: FragilityPassport | None,
    product: Product | None,
) -> RiskAssessment:
    behavior_codes = [b.code for b in behaviors]

    ml_score = _ml_reported_score(detection, behaviors)
    severity_score = max((b.default_severity for b in behaviors), default=1) * 20
    confidence_score = detection.confidence * 100

    # Blend: trust the upstream model most, but let the known behavior
    # severity and the model's own stated confidence pull the number too —
    # a HIGH claim made at 0.3 confidence shouldn't score the same as one at 0.95.
    combined = 0.5 * ml_score + 0.3 * severity_score + 0.2 * confidence_score

    violations = check_contract_violations(detection, behavior_codes, passport, product)
    if violations:
        # A confirmed contract breach isn't "maybe risky" — bump a full tier.
        combined = min(100.0, combined + 20.0)

    risk_level = determine_risk_level(combined)

    return RiskAssessment(
        risk_score=round(combined, 1),
        risk_level=risk_level,
        contract_clause_violated=" | ".join(violations) if violations else None,
        estimated_exposure_inr=estimate_exposure_inr(product, risk_level),
        violations=violations,
    )
