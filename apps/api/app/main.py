from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.routes.health import router as health_router


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    configure_logging(log_level=app_settings.log_level)

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
    )
    app.state.settings = app_settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)

    logger = logging.getLogger(__name__)
    logger.info(
        "application_started",
        extra={
            "environment": app_settings.app_env,
            "cors_allowed_origins": app_settings.cors_allowed_origins,
        },
    )

    return app


app = create_app()
