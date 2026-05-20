from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import Settings
from app.core.dependencies import get_app_settings
from app.schemas.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter(tags=["system"])


async def get_health_service(
    settings: Settings = Depends(get_app_settings),
) -> HealthService:
    return HealthService(settings=settings)


@router.get("/health", response_model=HealthResponse)
async def health(
    health_service: HealthService = Depends(get_health_service),
) -> HealthResponse:
    status = health_service.get_health_status()
    return HealthResponse(
        status=status.status,
        service=status.service,
        environment=status.environment,
        version=status.version,
    )
