"""The /events ingestion contract: what a raw ML/VLM detection looks like
coming IN to the backend, before the risk engine touches it.

Field names deliberately match ml/vlm's existing notebook output 1:1
(event_id, start_time, end_time, behavior, risk_level, risk_score, evidence,
potential_consequence, recommended_action, confidence, status) so that file
can be posted here with zero translation. Kinetic/spatial fields are
additions the DS/ML behavior modules (ml/behavior/*) are expected to send
once built. See docs/ml-backend-contract.md for the full write-up.

Everything here is treated as untrusted: this schema only checks shape and
range. Business-rule checks that need database context (e.g. "does this SKU
exist", "is this timestamp inside the video's real duration") happen in
event_service, not here.
"""
from pydantic import BaseModel, Field, field_validator

from app.core.constants import BEHAVIOR_CODES, EVENT_STATUSES, RISK_LEVELS


class DetectionIn(BaseModel):
    event_id: str | None = Field(default=None, description="Upstream event id, e.g. 'EVT_001'. Generated if absent.")

    # Where this happened.
    video_id: int | None = None
    source_clip_ref: str | None = Field(default=None, description="Filename or clip id if video_id is unknown yet.")
    dock: str | None = None

    # What product was involved (either works; sku is preferred since that's
    # what a QR scan / the VLM's product-identification step would return).
    product_sku: str | None = None
    product_id: int | None = None

    # When, within the clip. Accepts "mm:ss" (matches the VLM notebook) or a
    # plain number of seconds — event_service.parse_timecode() normalizes it.
    start_time: str | float
    end_time: str | float

    # What happened. Multi-label: the master plan's evidence showed one
    # timestamp can carry 2+ simultaneous behaviors.
    behavior: list[str] = Field(min_length=1)

    # The ML/VLM layer's own read on risk. The backend recalibrates this
    # against the product's Fragility Passport rather than trusting it as-is.
    risk_level: str | None = None
    risk_score: float | None = Field(default=None, ge=0, le=100)
    confidence: float = Field(ge=0, le=1)

    evidence: str | None = Field(default=None, description="Plain-language description of what was seen.")
    potential_consequence: list[str] | None = None
    recommended_action: str | None = None
    status: str = "observed_behaviour"

    # Kinetic module fields (ml/behavior/kinetic.py).
    tilt_deg: float | None = Field(default=None, ge=0, le=180)
    drop_height_cm: float | None = Field(default=None, ge=0)
    velocity_mps: float | None = Field(default=None, ge=0)
    impact_deceleration_mps2: float | None = Field(default=None, ge=0)

    # Static/configuration module fields (ml/behavior/stacking.py, spatial.py).
    overlap_ratio: float | None = Field(default=None, ge=0, le=1)
    overlap_duration_seconds: float | None = Field(default=None, ge=0)

    # Optional path to a saved evidence frame/clip (see app.utils.file_utils).
    evidence_frame_path: str | None = None

    @field_validator("behavior")
    @classmethod
    def validate_behavior_codes(cls, v: list[str]) -> list[str]:
        unknown = sorted(set(v) - BEHAVIOR_CODES)
        if unknown:
            raise ValueError(
                f"Unknown behavior code(s) {unknown}. Must be one of {sorted(BEHAVIOR_CODES)}"
            )
        return v

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, v: str | None) -> str | None:
        if v is not None and v.upper() not in RISK_LEVELS:
            raise ValueError(f"risk_level must be one of {RISK_LEVELS}")
        return v.upper() if v else v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in EVENT_STATUSES:
            raise ValueError(f"status must be one of {EVENT_STATUSES}")
        return v
