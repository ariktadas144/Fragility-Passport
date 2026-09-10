"""The supervisor Q&A assistant. Mirrors ml/vlm's notebook's own query
routing philosophy exactly: (1) refuse questions the system has no grounded
source for, (2) answer straightforward questions directly from the event
log with no AI call at all, (3) only hand genuinely interpretive questions
to a real language model.

Workstream 2 owns the actual Gemini connection. This file never imports a
specific AI vendor — it defines ReasoningClient, an abstract "socket" that
Workstream 2's real implementation plugs into. Until that's wired up,
NullReasoningClient is used, which just says so honestly.
"""
import re
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.core.constants import UNAVAILABLE_DATA_KEYWORDS
from app.models.behavior import Behavior
from app.models.event import Event
from app.models.event_behavior import EventBehavior
from app.schemas.assistant import AssistantAnswer
from app.schemas.event import EventListItem
from app.services import event_service

EVENT_ID_PATTERN = re.compile(r"\bEVT_[A-Z0-9]+\b", re.IGNORECASE)


class ReasoningClient(ABC):
    """The interface any real LLM integration (Gemini, etc.) must implement.
    Workstream 2 writes a concrete subclass elsewhere and passes it into
    answer_question() — this file has no idea which AI vendor is behind it."""

    @abstractmethod
    def answer(self, question: str, context_events: list[Event]) -> str:
        """Given the question and the relevant events as grounding context,
        return a plain-language answer."""
        raise NotImplementedError


class NullReasoningClient(ReasoningClient):
    """Default stand-in used until Workstream 2's real client is wired up."""

    def answer(self, question: str, context_events: list[Event]) -> str:
        return (
            "AI reasoning isn't connected yet in this environment. "
            "This question needs interpretation beyond a direct lookup, "
            "so it would normally be routed to the VLM reasoning layer."
        )


def _event_to_list_item(event: Event) -> EventListItem:
    return EventListItem(
        id=event.id,
        public_id=event.public_id,
        dock=event.dock,
        start_time_seconds=event.start_time_seconds,
        risk_level=event.risk_level,
        risk_score=event.risk_score,
        status=event.status,
        behaviors=[link.behavior.code for link in event.behavior_links],
    )


def is_unavailable_data_question(question: str) -> bool:
    lowered = question.lower()
    return any(keyword in lowered for keyword in UNAVAILABLE_DATA_KEYWORDS)


def _try_answer_locally(db: Session, question: str) -> AssistantAnswer | None:
    """Pattern-matches common factual questions and answers them straight
    from the database. Returns None if the question doesn't match anything
    this function knows how to look up directly."""
    lowered = question.lower()

    id_match = EVENT_ID_PATTERN.search(question)
    if id_match:
        event = event_service.get_event_by_public_id(db, id_match.group(0).upper())
        data = event_service.to_event_read_dict(event)
        return AssistantAnswer(
            answer=(
                f"{event.public_id}: {event.risk_level} risk (score {event.risk_score}), "
                f"dock {event.dock or 'unknown'}, status {event.status}. "
                f"{event.evidence_description or ''}"
            ).strip(),
            source="local",
            data=data,
        )

    if "how many" in lowered and "event" in lowered:
        count = db.query(Event).count()
        return AssistantAnswer(answer=f"{count} events have been logged.", source="local", data={"count": count})

    if "high" in lowered and "risk" in lowered and ("which" in lowered or "list" in lowered or "what" in lowered):
        events = db.query(Event).filter(Event.risk_level.in_(["HIGH", "CRITICAL"])).order_by(
            Event.created_at.desc()
        ).all()
        items = [_event_to_list_item(e) for e in events]
        return AssistantAnswer(
            answer=f"{len(items)} HIGH/CRITICAL risk event(s): " + ", ".join(i.public_id for i in items),
            source="local",
            data=[i.model_dump() for i in items],
        )

    if "highest" in lowered and "risk" in lowered:
        event = db.query(Event).order_by(Event.risk_score.desc()).first()
        if event is None:
            return AssistantAnswer(answer="No events logged yet.", source="local")
        return AssistantAnswer(
            answer=f"{event.public_id} has the highest risk score ({event.risk_score}, {event.risk_level}).",
            source="local",
            data=_event_to_list_item(event).model_dump(),
        )

    if "timeline" in lowered:
        events = db.query(Event).order_by(Event.created_at.asc()).all()
        items = [_event_to_list_item(e) for e in events]
        return AssistantAnswer(
            answer=f"Timeline of {len(items)} event(s), oldest first.",
            source="local",
            data=[i.model_dump() for i in items],
        )

    if "which dock" in lowered or ("dock" in lowered and "most" in lowered):
        rows = db.query(Event.dock).all()
        from collections import Counter

        counts = Counter(dock or "unknown" for (dock,) in rows)
        if not counts:
            return AssistantAnswer(answer="No events logged yet.", source="local")
        top_dock, top_count = counts.most_common(1)[0]
        return AssistantAnswer(
            answer=f"Dock {top_dock} has the most events ({top_count}).",
            source="local",
            data=dict(counts),
        )

    if "behaviour" in lowered or "behavior" in lowered:
        rows = db.query(Behavior.label).join(EventBehavior, EventBehavior.behavior_id == Behavior.id).all()
        labels = sorted({label for (label,) in rows})
        if not labels:
            return AssistantAnswer(answer="No behaviors detected yet.", source="local")
        return AssistantAnswer(answer="Detected behaviors: " + ", ".join(labels), source="local", data=labels)

    return None


def answer_question(
    db: Session, question: str, reasoning_client: ReasoningClient | None = None
) -> AssistantAnswer:
    """The single entry point POST /assistant/query calls."""
    if is_unavailable_data_question(question):
        return AssistantAnswer(
            answer="I could not find this information in the available event logs.",
            source="unavailable",
        )

    local_answer = _try_answer_locally(db, question)
    if local_answer is not None:
        return local_answer

    client = reasoning_client or NullReasoningClient()
    context_events = db.query(Event).order_by(Event.created_at.desc()).limit(50).all()
    return AssistantAnswer(answer=client.answer(question, context_events), source="llm")
