from __future__ import annotations

from fastapi import Request

from app.core.config import Settings, get_settings


async def get_app_settings(request: Request) -> Settings:
    settings = getattr(request.app.state, "settings", None)
    if isinstance(settings, Settings):
        return settings
    return get_settings()
