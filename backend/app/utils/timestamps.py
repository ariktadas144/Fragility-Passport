"""Timecode parsing/formatting and a shared UTC-now helper.

Mirrors the validation philosophy in ml/vlm's notebook: never trust a
timestamp blindly. Accepts both the VLM's "mm:ss" strings and plain numeric
seconds (what a frame-by-frame kinetic/spatial module would naturally send).
"""
from datetime import datetime, timezone

from app.core.exceptions import ValidationFailedError


def utcnow() -> datetime:
    """Naive UTC datetime, used for every timestamp column in the app.

    Deliberately naive (no tzinfo) rather than timezone-aware: SQLite has no
    real datetime type, so it stores whatever string SQLAlchemy serializes.
    Mixing aware and naive datetimes would produce inconsistent string
    formats and silently-wrong comparisons (e.g. the escalation-timer query
    in alert_service). Keeping everything naive-UTC keeps every stored value
    in the same sortable ISO format.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_timecode(value: str | float) -> float:
    """Accepts "12", "12.5", "00:12", "01:02:03", or a bare number; returns seconds."""
    if isinstance(value, (int, float)):
        return float(value)

    text = value.strip()
    if ":" not in text:
        try:
            return float(text)
        except ValueError as exc:
            raise ValidationFailedError(f"Could not parse timecode '{value}'") from exc

    parts = text.split(":")
    if len(parts) not in (2, 3):
        raise ValidationFailedError(f"Could not parse timecode '{value}'")
    try:
        parts_f = [float(p) for p in parts]
    except ValueError as exc:
        raise ValidationFailedError(f"Could not parse timecode '{value}'") from exc

    seconds = 0.0
    for part in parts_f:
        seconds = seconds * 60 + part
    return seconds


def format_seconds(seconds: float) -> str:
    """Seconds -> "mm:ss", for display in reports/assistant answers."""
    total = int(round(seconds))
    minutes, secs = divmod(total, 60)
    return f"{minutes:02d}:{secs:02d}"


def validate_within_duration(start_seconds: float, end_seconds: float, duration_seconds: float | None) -> None:
    if end_seconds < start_seconds:
        raise ValidationFailedError(f"end_time ({end_seconds}s) is before start_time ({start_seconds}s)")
    if duration_seconds is not None and (start_seconds > duration_seconds or end_seconds > duration_seconds):
        raise ValidationFailedError(
            f"Timestamps ({start_seconds}-{end_seconds}s) fall outside the video's "
            f"real duration ({duration_seconds}s)"
        )
