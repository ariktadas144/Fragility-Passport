"""
Fragility Passport lookup service.

Reads from data/seed/fragility_passports.json for now. Whoever owns the
database layer can swap this for a real DB-backed lookup (e.g. querying
the fragility_passport SQLAlchemy model) -- keep the same function
signatures and the API layer (api/passports.py) doesn't need to change.
"""

import json
from pathlib import Path

_CONTRACTS_PATH = Path(__file__).parent.parent.parent.parent / "data" / "seed" / "fragility_passports.json"


def load_contracts() -> dict:
    with open(_CONTRACTS_PATH) as f:
        return json.load(f)


def get_contract(product_code: str) -> dict | None:
    contracts = load_contracts()
    return contracts.get(product_code.upper())


def check_violation(product_code: str, observed: dict) -> dict:
    """
    observed = {"tilt_degrees": float, "drop_height_cm": float, "was_dragged": bool}
    """
    contract = get_contract(product_code)
    if not contract:
        return {"error": f"No contract found for product code '{product_code}'"}

    violations = []
    if observed.get("tilt_degrees", 0) > contract["max_tilt_degrees"]:
        violations.append(
            f"Tilt {observed['tilt_degrees']}\u00b0 exceeds max {contract['max_tilt_degrees']}\u00b0"
        )
    if observed.get("drop_height_cm", 0) > contract["max_drop_height_cm"]:
        violations.append(
            f"Drop height {observed['drop_height_cm']}cm exceeds max {contract['max_drop_height_cm']}cm"
        )
    if observed.get("was_dragged") and not contract["drag_allowed"]:
        violations.append("Dragging detected but not permitted for this product")

    return {
        "product_code": product_code,
        "product_name": contract["product_name"],
        "violations": violations,
        "compliant": len(violations) == 0,
    }
