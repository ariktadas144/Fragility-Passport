"""Small helpers for the service layer. Field-level validation (types,
ranges, allowed values) already lives in app.schemas — these are for plain
data cleanup that doesn't need a Pydantic validator."""


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
