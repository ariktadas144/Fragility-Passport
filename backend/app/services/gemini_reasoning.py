"""Gemini-backed ReasoningClient for the supervisor assistant.

This is the concrete implementation the docstring in assistant_service.py
anticipated ("Workstream 2 writes a concrete subclass elsewhere"). It is
STRICTLY GROUNDED: Gemini is given only the relevant slice of the event log
and instructed to answer from that alone, or to decline. It never sees the
whole database and is told not to use outside knowledge.

If the Gemini call fails (no key, network, rate limit, timeout, bad output)
the caller falls back to NullReasoningClient — see
assistant_service.answer_question — so a live demo never 500s on this path.
"""
from __future__ import annotations

import json
import os

from app.core.logging import get_logger
from app.models.event import Event
from app.schemas.assistant import AssistantAnswer
from app.services.assistant_service import NullReasoningClient, ReasoningClient

logger = get_logger(__name__)

GEMINI_MODEL = "gemini-3.1-flash-lite"
REQUEST_TIMEOUT_MS = 20_000

# Gemini returns this token verbatim when the provided events don't support
# an answer. Mapped to the "unavailable" / "not tracked" badge.
_INSUFFICIENT = "INSUFFICIENT_CONTEXT"

_SYSTEM_PROMPT = """\
You are a warehouse operations assistant for supervisors. You answer \
questions about handling incidents.

STRICT RULES — follow them exactly:
- Use ONLY the facts in the EVENTS JSON below. Do not use any outside \
knowledge, industry assumptions, or general reasoning beyond what the \
EVENTS state.
- If the EVENTS do not contain enough information to answer the question, \
reply with EXACTLY this token and nothing else: {insufficient}
- Never invent or guess an event id, SKU, product name, monetary value, \
count, timestamp, dock, or person. If it is not in the EVENTS, it is not \
available.
- Do not identify or speculate about individual workers.
- Be concise: 1-3 sentences. Quote the relevant event's public_id when you \
can.

EVENTS (JSON array, the only data you may use):
{events}

QUESTION: {question}
"""


def _serialize_event(event: Event) -> dict:
    """Compact, JSON-safe view of one Event for grounding context."""
    return {
        "public_id": event.public_id,
        "dock": event.dock,
        "risk_level": event.risk_level,
        "risk_score": event.risk_score,
        "status": event.status,
        "confidence": event.confidence,
        "start_time_seconds": event.start_time_seconds,
        "end_time_seconds": event.end_time_seconds,
        "behaviors": [link.behavior.code for link in event.behavior_links],
        "evidence": event.evidence_description,
        "contract_clause_violated": event.contract_clause_violated,
        "estimated_exposure_inr": event.estimated_exposure_inr,
        "recommended_action": event.recommended_action,
        "product": (
            {"sku": event.product.sku, "name": event.product.name}
            if event.product
            else None
        ),
    }


def _api_key() -> str | None:
    # get_settings() reads backend/.env; env var and an explicit dotenv load
    # are belt-and-suspenders for other working directories.
    from app.config import get_settings

    key = get_settings().gemini_api_key or os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    try:
        from pathlib import Path

        from dotenv import dotenv_values

        env_path = Path(__file__).resolve().parents[2] / ".env"
        return dotenv_values(env_path).get("GEMINI_API_KEY")
    except Exception:  # noqa: BLE001
        return None


class GeminiReasoningClient(ReasoningClient):
    """Strictly-grounded Gemini reasoning over a slice of the event log."""

    def __init__(self, model: str = GEMINI_MODEL) -> None:
        self._model = model
        self._client = None  # lazily created so a missing key doesn't error at import

    def _get_client(self):
        if self._client is None:
            from google import genai
            from google.genai import types

            api_key = _api_key()
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY is not configured")
            self._client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(
                    timeout=REQUEST_TIMEOUT_MS,
                    retry_options=types.HttpRetryOptions(attempts=3, initial_delay=1.0, max_delay=8.0),
                ),
            )
        return self._client

    def answer(self, question: str, context_events: list[Event]) -> AssistantAnswer:
        from google.genai import types

        events_json = json.dumps(
            [_serialize_event(e) for e in context_events], indent=2, default=str
        )
        prompt = _SYSTEM_PROMPT.format(
            insufficient=_INSUFFICIENT, events=events_json, question=question
        )

        client = self._get_client()
        response = client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )

        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("Gemini returned an empty response")

        # Decline -> the frontend's "not tracked" badge.
        normalized = text.strip().strip(".").upper()
        if normalized == _INSUFFICIENT or text.startswith(_INSUFFICIENT):
            return AssistantAnswer(
                answer="I could not find this information in the available event logs.",
                source="unavailable",
            )

        return AssistantAnswer(answer=text, source="llm")


def build_default_reasoning_client() -> ReasoningClient:
    """A GeminiReasoningClient if a key is configured, else the honest stub."""
    if _api_key():
        return GeminiReasoningClient()
    logger.info("No GEMINI_API_KEY configured; assistant uses NullReasoningClient")
    return NullReasoningClient()
