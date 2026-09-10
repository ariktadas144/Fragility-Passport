"""Import every model module here so app.database.database.init_db()'s
Base.metadata.create_all() knows about all of them, and so SQLAlchemy can
resolve the string-based relationship() references between files (e.g.
Event.video -> "Video") once every class has actually been loaded."""

from app.models.product import Product
from app.models.fragility_passport import FragilityPassport
from app.models.behavior import Behavior
from app.models.video import Video
from app.models.event import Event
from app.models.event_behavior import EventBehavior
from app.models.evidence import Evidence
from app.models.alert import Alert

__all__ = [
    "Product",
    "FragilityPassport",
    "Behavior",
    "Video",
    "Event",
    "EventBehavior",
    "Evidence",
    "Alert",
]
