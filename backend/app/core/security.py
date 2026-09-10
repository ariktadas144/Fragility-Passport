"""Minimal shared-secret guard for write endpoints.

Hackathon scope: no user accounts. If APP_SETTINGS.api_key is set, mutating
requests must send it via the X-API-Key header; if unset (the default), the
check is a no-op so local/demo usage needs no setup.
"""
from fastapi import Header, HTTPException, status

from app.config import get_settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not settings.api_key:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
