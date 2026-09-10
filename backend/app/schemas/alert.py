from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    status: str
    created_at: datetime
    acknowledged_at: datetime | None
    acknowledged_by: str | None
    escalated_at: datetime | None


class AlertAcknowledge(BaseModel):
    acknowledged_by: str = Field(min_length=1, max_length=128, description="Supervisor name/id acknowledging this alert.")
