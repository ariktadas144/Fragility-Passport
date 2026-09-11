"""Fragility Passport lookup — including GET /passports/scan/{code}, the
live QR-scan endpoint Workstream 5's booth demo hits: scan a box, its
handling contract loads instantly."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.exceptions import DomainError
from app.core.security import require_api_key
from app.database.database import get_db
from app.schemas.passport import FragilityPassportCreate, FragilityPassportRead
from app.services import passport_service

router = APIRouter(prefix="/passports", tags=["passports"])


@router.get("/scan/{code}", response_model=FragilityPassportRead)
def scan_passport(code: str, db: Session = Depends(get_db)):
    """`code` is whatever the QR code on the box encodes — the product SKU."""
    result = passport_service.get_passport_by_sku(db, code)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No Fragility Passport found for code '{code}'")
    _, passport = result
    return passport


@router.get("/{product_id}", response_model=FragilityPassportRead)
def get_passport(product_id: int, db: Session = Depends(get_db)):
    passport = passport_service.get_passport_for_product(db, product_id)
    if passport is None:
        raise HTTPException(status_code=404, detail=f"No Fragility Passport found for product {product_id}")
    return passport


@router.post("", response_model=FragilityPassportRead, dependencies=[Depends(require_api_key)])
def create_passport(payload: FragilityPassportCreate, db: Session = Depends(get_db)):
    try:
        return passport_service.create_passport(db, payload)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
