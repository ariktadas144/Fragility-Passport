from pydantic import BaseModel, ConfigDict


class BehaviorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    label: str
    category: str
    default_severity: int
