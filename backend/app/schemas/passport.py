from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import REQUIRED_ORIENTATIONS


class FragilityPassportBase(BaseModel):
    max_tilt_deg: float = Field(default=90.0, ge=0, le=180)
    max_drop_height_cm: float = Field(default=0.0, ge=0)
    required_orientation: str = Field(default="ANY")
    max_stack_weight_kg: float = Field(default=0.0, ge=0)
    drag_allowed: bool = True
    throw_allowed: bool = False
    notes: str | None = None

    @field_validator("required_orientation")
    @classmethod
    def validate_orientation(cls, v: str) -> str:
        v = v.upper()
        if v not in REQUIRED_ORIENTATIONS:
            raise ValueError(f"required_orientation must be one of {REQUIRED_ORIENTATIONS}")
        return v


class FragilityPassportCreate(FragilityPassportBase):
    product_id: int


class FragilityPassportRead(FragilityPassportBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
