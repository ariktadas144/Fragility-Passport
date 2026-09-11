"""Unit tests for Fragility Passport lookup + creation."""
import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.models.product import Product
from app.schemas.passport import FragilityPassportCreate
from app.services import passport_service


def _make_product(db_session, sku="ABC-123") -> Product:
    product = Product(sku=sku, name="KD Panel Cupboard", category="kd-panel-furniture", declared_value_inr=8000)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def _passport_payload(product_id: int) -> FragilityPassportCreate:
    return FragilityPassportCreate(
        product_id=product_id,
        max_tilt_deg=40,
        max_drop_height_cm=5,
        required_orientation="UPRIGHT",
        max_stack_weight_kg=10,
        drag_allowed=False,
        throw_allowed=False,
    )


def test_get_product_by_sku_returns_none_when_missing(db_session):
    assert passport_service.get_product_by_sku(db_session, "does-not-exist") is None


def test_create_and_fetch_passport(db_session):
    product = _make_product(db_session)
    created = passport_service.create_passport(db_session, _passport_payload(product.id))
    assert created.product_id == product.id

    fetched = passport_service.get_passport_for_product(db_session, product.id)
    assert fetched is not None
    assert fetched.max_tilt_deg == 40


def test_create_passport_for_unknown_product_raises(db_session):
    with pytest.raises(NotFoundError):
        passport_service.create_passport(db_session, _passport_payload(product_id=999))


def test_create_duplicate_passport_raises_conflict(db_session):
    product = _make_product(db_session)
    passport_service.create_passport(db_session, _passport_payload(product.id))
    with pytest.raises(ConflictError):
        passport_service.create_passport(db_session, _passport_payload(product.id))


def test_get_passport_by_sku_scan_lookup(db_session):
    product = _make_product(db_session)
    passport_service.create_passport(db_session, _passport_payload(product.id))

    result = passport_service.get_passport_by_sku(db_session, "ABC-123")
    assert result is not None
    fetched_product, fetched_passport = result
    assert fetched_product.sku == "ABC-123"
    assert fetched_passport.required_orientation == "UPRIGHT"

    assert passport_service.get_passport_by_sku(db_session, "NOPE") is None
