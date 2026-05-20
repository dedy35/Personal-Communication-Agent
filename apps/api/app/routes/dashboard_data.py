from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.schemas.dashboard import (
    ConversationsResponse,
    DashboardCountsResponse,
    DraftsResponse,
    MessagesResponse,
    PlatformStatusesResponse,
    STATUS_VALUES,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(tags=["dashboard"])


async def get_dashboard_service(db: Session = Depends(get_db_session)) -> DashboardService:
    return DashboardService(db=db)


@router.get("/platforms/statuses", response_model=PlatformStatusesResponse)
async def list_platform_statuses(
    service: DashboardService = Depends(get_dashboard_service),
) -> PlatformStatusesResponse:
    return PlatformStatusesResponse(items=service.list_platform_statuses())


@router.get("/conversations", response_model=ConversationsResponse)
async def list_conversations(
    platform: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: DashboardService = Depends(get_dashboard_service),
) -> ConversationsResponse:
    if status is not None and status not in STATUS_VALUES:
        # Return empty to keep UI robust on invalid query value.
        return ConversationsResponse(items=[], total=0)

    items, total = service.list_conversations(platform=platform, status=status, limit=limit, offset=offset)
    return ConversationsResponse(items=items, total=total)


@router.get("/conversations/{conversation_id}/messages", response_model=MessagesResponse)
async def list_messages(
    conversation_id: int,
    limit: int = Query(default=200, ge=1, le=500),
    service: DashboardService = Depends(get_dashboard_service),
) -> MessagesResponse:
    return MessagesResponse(items=service.list_messages(conversation_id=conversation_id, limit=limit))


@router.get("/drafts", response_model=DraftsResponse)
async def list_drafts(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: DashboardService = Depends(get_dashboard_service),
) -> DraftsResponse:
    items, total = service.list_drafts(status=status, limit=limit, offset=offset)
    return DraftsResponse(items=items, total=total)


@router.get("/dashboard/counts", response_model=DashboardCountsResponse)
async def dashboard_counts(
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardCountsResponse:
    return service.get_dashboard_counts()
