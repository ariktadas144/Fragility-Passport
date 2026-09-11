from typing import Any, Literal

from pydantic import BaseModel


class AssistantQuery(BaseModel):
    question: str


class AssistantAnswer(BaseModel):
    answer: str
    # "local": answered straight from the event log, no LLM call.
    # "llm": routed to the pluggable ReasoningClient (Workstream 2's Gemini call).
    # "unavailable": grounded refusal — the data simply isn't tracked.
    source: Literal["local", "llm", "unavailable"]
    data: Any | None = None
