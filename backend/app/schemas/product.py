from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    sku: str = Field(max_length=64)
    name: str = Field(max_length=255)
    category: str = Field(max_length=64)
    declared_value_inr: float = Field(default=0.0, ge=0)


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
