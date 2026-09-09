from fastapi import APIRouter, HTTPException
from app.services import passport_service

router = APIRouter()


@router.get("/passports/{product_id}")
async def get_passport(product_id: str):
    contract = passport_service.get_contract(product_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"No contract for '{product_id}'")
    return contract


@router.post("/passports/{product_id}/check")
async def check_passport(product_id: str, observed: dict):
    result = passport_service.check_violation(product_id, observed)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
