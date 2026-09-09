"""
Conversational assistant reasoning -- grounded Q&A over the event log.

STUB: currently a trivial keyword match. VLM workstream owns replacing
query_assistant() with a real LLM call. Keep it grounded in event_log
(RAG-lite: pass relevant events as context) -- don't let the model invent
numbers that aren't in the actual data.
"""

from typing import List


def query_assistant(question: str, event_log: List[dict]) -> str:
    q = question.lower()
    high_risk = [e for e in event_log if e.get("risk_level") in ("high", "critical")]
    if "high risk" in q or "critical" in q:
        return f"There are {len(high_risk)} high/critical risk events in this session. TODO: replace with real grounded LLM answer."
    return "TODO: wire this up to a real LLM call grounded in the event log -- this is a placeholder response."
