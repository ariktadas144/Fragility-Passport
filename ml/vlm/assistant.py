"""
Warehouse AI assistant -- grounded Q&A over the Gemini-generated event log.

Converted from the notebook's cells 17-20. Three-step routing, unchanged:
  1. Answer directly from the event log if possible (no API call).
  2. Refuse gracefully if the question asks for data the log doesn't have
     (SKU, price, injury, etc.) -- prevents hallucination.
  3. Only call Gemini for genuine reasoning questions.

This REPLACES the old ml/vlm/reasoning.py stub -- that was a placeholder
before this real implementation existed.
"""

import re
import json

from ml.vlm.gemini_analysis import timestamp_to_seconds, _get_client, GEMINI_MODEL
from google.genai import types

UNAVAILABLE_PATTERNS = [
    "monetary value", "product value", "price",
    "cost of the product", "sku", "product sku",
    "exact weight", "product weight",
    "who was responsible", "responsible for the incident",
    "who caused", "was anyone injured", "anyone injured",
    "injury", "drop height", "exact drop height",
    "financial loss", "loss amount",
]


def is_unavailable_question(question: str) -> bool:
    q = question.lower()
    return any(pattern in q for pattern in UNAVAILABLE_PATTERNS)


def direct_event_answer(question: str, data: dict):
    q = question.lower().strip()
    events = data.get("events", [])

    if any(x in q for x in ["how many events", "number of events", "total events", "count of events"]):
        return f"There are {len(events)} detected event(s) in the available event log."

    if any(x in q for x in ["what risky behaviours", "which risky behaviours",
                             "what behaviours were detected", "which behaviours were detected"]):
        behaviours = []
        for e in events:
            for b in e.get("behavior", []):
                if b not in behaviours:
                    behaviours.append(b)
        if not behaviours:
            return "No predefined risky behaviours were detected."
        return "Detected risky behaviours:\n\n" + "\n".join(f"\u2022 {b}" for b in behaviours)

    if "high risk" in q or "high-risk" in q:
        high = [e for e in events if e.get("risk_level", "").upper() == "HIGH"]
        if not high:
            return "No HIGH-risk events were found in the available event logs."
        return "HIGH-risk events:\n\n" + "\n\n".join(
            f"\u2022 {e['event_id']}\n"
            f"  Timestamp: {e['start_time']} - {e['end_time']}\n"
            f"  Behaviour: {', '.join(e['behavior'])}\n"
            f"  Risk Score: {e['risk_score']}"
            for e in high
        )

    if any(x in q for x in ["highest risk", "highest-risk", "highest risk score", "most risky event"]):
        if not events:
            return "No events are available."
        e = max(events, key=lambda x: float(x.get("risk_score", 0)))
        return (
            f"The highest-risk event is {e['event_id']}.\n\n"
            f"Timestamp: {e['start_time']} - {e['end_time']}\n"
            f"Behaviour: {', '.join(e['behavior'])}\n"
            f"Risk Level: {e['risk_level']}\n"
            f"Risk Score: {e['risk_score']}\n"
            f"Confidence: {e['confidence']}"
        )

    if "timeline" in q or "all incidents" in q:
        if not events:
            return "No incidents were detected."
        ordered = sorted(events, key=lambda x: timestamp_to_seconds(x["start_time"]))
        return "Incident timeline:\n\n" + "\n".join(
            f"\u2022 {e['event_id']}: {e['start_time']} - {e['end_time']} \u2192 {', '.join(e['behavior'])}"
            for e in ordered
        )

    match = re.search(r"\bEVT[_-]?\d+\b", question, re.IGNORECASE)
    if match:
        wanted = match.group(0).replace("-", "_").upper()
        for e in events:
            if e.get("event_id", "").upper() == wanted:
                rules = "\n".join(
                    f"\u2022 {r['rule_id']}: {r['rule']}" for r in e.get("handling_rules", [])
                ) or "No mapped handling rule available."
                return (
                    f"Event {wanted}\n\n"
                    f"Timestamp: {e.get('start_time')} - {e.get('end_time')}\n"
                    f"Behaviour: {', '.join(e.get('behavior', []))}\n"
                    f"Risk Level: {e.get('risk_level')}\n"
                    f"Risk Score: {e.get('risk_score')}\n"
                    f"Confidence: {e.get('confidence')}\n"
                    f"Status: {e.get('status')}\n\n"
                    f"Evidence:\n{e.get('evidence', 'Not available')}\n\n"
                    f"Potential Consequence:\n{', '.join(e.get('potential_consequence', []))}\n\n"
                    f"Recommended Action:\n{e.get('recommended_action', 'Not available')}\n\n"
                    f"Handling Rules:\n{rules}"
                )
        return f"I could not find {wanted} in the available event logs."

    return None


def gemini_reasoning_answer(question: str, data: dict) -> str:
    context = json.dumps(data, indent=2)
    prompt = f"""
You are an AI Warehouse Operations Assistant.

Use ONLY the warehouse event data below.

WAREHOUSE EVENT DATA:
{context}

USER QUESTION:
{question}

Rules:
- Never invent facts.
- Never invent SKU, weight, price, monetary value, injury, identity,
  exact measurements, or facts not present in the event data.
- Distinguish observed behaviour, potential risk, and confirmed damage.
- Confirmed damage may only be stated if the event status is confirmed_damage.
- If requested information is not present, say exactly:
  "I could not find this information in the available event logs."
- Be concise and operationally useful.
"""
    try:
        client = _get_client()
        result = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=1)),
            ),
        )
        return result.text if result.text else "No answer was returned."
    except Exception as e:
        error_text = str(e)
        if "503" in error_text or "UNAVAILABLE" in error_text:
            return "Gemini is temporarily unavailable. JSON-based event questions still work locally."
        if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
            return "Gemini API quota/rate limit was reached. JSON-based event questions still work locally."
        return f"Gemini reasoning request failed: {error_text}"


def warehouse_assistant(question: str, data: dict) -> str:
    direct = direct_event_answer(question, data)
    if direct is not None:
        return direct
    if is_unavailable_question(question):
        return "I could not find this information in the available event logs."
    return gemini_reasoning_answer(question, data)
