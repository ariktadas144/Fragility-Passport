"""Shared vocabularies and thresholds used across the backend.

The behavior codes below are the exact machine-readable set produced by the
VLM reasoning layer (see ml/vlm/README.md) plus the kinetic/spatial codes the
DS/ML behavior modules (ml/behavior/*) are expected to emit. Keeping this list
the single source of truth is what lets /events accept output from either
layer without translation.
"""

# code -> (human label, category, default severity 1-5)
BEHAVIOR_VOCABULARY: dict[str, dict] = {
    "product_dropped": {"label": "Dropping product", "category": "kinetic", "default_severity": 4},
    "product_dragged": {"label": "Dragging carton/KD packet", "category": "kinetic", "default_severity": 3},
    "product_thrown": {"label": "Throwing/dropping product", "category": "kinetic", "default_severity": 5},
    "product_rolling": {"label": "Rolling carton/mattress", "category": "kinetic", "default_severity": 3},
    "rough_handling": {"label": "Improper/manual mishandling", "category": "kinetic", "default_severity": 3},
    "improper_stacking": {"label": "Heavy-on-light stacking", "category": "static", "default_severity": 3},
    "unstable_stacking": {"label": "Unstable stack configuration", "category": "static", "default_severity": 3},
    "product_outside_designated_area": {
        "label": "Product outside designated area", "category": "static", "default_severity": 2,
    },
    "improper_equipment_usage": {"label": "Wrong strap/equipment use", "category": "kinetic", "default_severity": 3},
    "unsafe_loading_sequence": {"label": "Unsafe loading sequence", "category": "static", "default_severity": 3},
    # Additional codes surfaced by the master-plan ground-truth taxonomy that
    # don't map 1:1 onto the VLM's list above.
    "wrong_orientation": {"label": "Vertical product kept horizontally", "category": "static", "default_severity": 4},
    "stepping_on_product": {"label": "Stepping on cartons", "category": "kinetic", "default_severity": 3},
    "dock_vehicle_gap": {"label": "Gap between dock and vehicle", "category": "static", "default_severity": 3},
    "uneven_dock_level": {"label": "Uneven dock level, no leveler", "category": "static", "default_severity": 2},
}

BEHAVIOR_CODES = frozenset(BEHAVIOR_VOCABULARY.keys())

RISK_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

# Numeric risk_score (0-100) lower bound for each level.
RISK_LEVEL_THRESHOLDS: dict[str, int] = {
    "LOW": 0,
    "MEDIUM": 40,
    "HIGH": 65,
    "CRITICAL": 85,
}

EVENT_STATUSES = ("observed_behaviour", "potential_risk", "confirmed_damage")

ALERT_STATUSES = ("ACTIVE", "ACKNOWLEDGED", "ESCALATED")

REQUIRED_ORIENTATIONS = ("UPRIGHT", "FLAT", "ANY")

# Multiplier applied to a product's declared value to produce the
# industry-indicative ₹ exposure estimate shown on the dashboard/report.
# NOT an audited figure — see docs/risk-engine.md.
EXPOSURE_MULTIPLIER_BY_RISK_LEVEL: dict[str, float] = {
    "LOW": 0.05,
    "MEDIUM": 0.15,
    "HIGH": 0.35,
    "CRITICAL": 0.65,
}

# Fields a supervisor might ask about that the system has no grounded source
# for. Mirrors the VLM notebook's "grounding" guard.
UNAVAILABLE_DATA_KEYWORDS = (
    "sku", "price", "cost", "monetary", "worth", "weight", "kg", "kilogram",
    "injury", "injured", "hurt", "who was", "which worker", "employee name",
)
