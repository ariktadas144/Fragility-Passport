"""Fragility Passport lookup + CRUD: the "handling contract" the loading-bay
camera checks real behavior against. get_passport_by_sku is what
GET /passports/scan/{code} calls for Workstream 5's live QR-scan demo."""
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.fragility_passport import FragilityPassport
from app.models.product import Product
from app.schemas.passport import FragilityPassportCreate


def get_product(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def get_product_by_sku(db: Session, sku: str) -> Product | None:
    return db.query(Product).filter(Product.sku == sku).first()


def get_passport_for_product(db: Session, product_id: int) -> FragilityPassport | None:
    return db.query(FragilityPassport).filter(FragilityPassport.product_id == product_id).first()


def get_passport_by_sku(db: Session, sku: str) -> tuple[Product, FragilityPassport] | None:
    """A QR code on a box encodes a SKU; this is what scanning it resolves to."""
    product = get_product_by_sku(db, sku)
    if product is None or product.passport is None:
        return None
    return product, product.passport


def create_passport(db: Session, payload: FragilityPassportCreate) -> FragilityPassport:
    product = get_product(db, payload.product_id)
    if product is None:
        raise NotFoundError(f"Product {payload.product_id} not found")
    if get_passport_for_product(db, payload.product_id) is not None:
        raise ConflictError(f"Product {payload.product_id} already has a Fragility Passport")

    passport = FragilityPassport(**payload.model_dump())
    db.add(passport)
    db.commit()
    db.refresh(passport)
    return passport
