"""Pydantic schemas: the shapes of data crossing the API boundary.

Unlike app.models (database tables), nothing here touches SQLAlchemy —
these are pure validation/serialization classes.
"""
from app.schemas.alert import AlertAcknowledge, AlertRead
from app.schemas.assistant import AssistantAnswer, AssistantQuery
from app.schemas.behavior import BehaviorRead
from app.schemas.dashboard import DashboardSummary, TrainingGapItem, TrainingGapResponse
from app.schemas.detection import DetectionIn
from app.schemas.event import EventListItem, EventRead
from app.schemas.passport import FragilityPassportCreate, FragilityPassportRead
from app.schemas.product import ProductCreate, ProductRead

__all__ = [
    "AlertAcknowledge",
    "AlertRead",
    "AssistantAnswer",
    "AssistantQuery",
    "BehaviorRead",
    "DashboardSummary",
    "TrainingGapItem",
    "TrainingGapResponse",
    "DetectionIn",
    "EventListItem",
    "EventRead",
    "FragilityPassportCreate",
    "FragilityPassportRead",
    "ProductCreate",
    "ProductRead",
]
