from __future__ import annotations

from app.core.config import Settings
from app.models.health import HealthStatus


class HealthService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def get_health_status(self) -> HealthStatus:
        return HealthStatus(
            status="ok",
            service=self._settings.app_name,
            environment=self._settings.app_env,
            version=self._settings.app_version,
        )
