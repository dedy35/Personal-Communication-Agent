from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.schemas.drafting import (
    DraftGenerateRequest,
    DraftGenerateResponse,
    DraftReviseRequest,
    DraftReviseResponse,
)
from app.services.draft_service import (
    ConversationNotFoundError,
    DraftNotFoundError,
    DraftService,
    MessageNotFoundError,
)

router = APIRouter(tags=["drafts"])


async def get_draft_service(db: Session = Depends(get_db_session)) -> DraftService:
    return DraftService(db=db)


@router.post("/drafts/generate", response_model=DraftGenerateResponse)
async def generate_draft(
    payload: DraftGenerateRequest,
    service: DraftService = Depends(get_draft_service),
) -> DraftGenerateResponse:
    try:
        return service.generate_draft(payload)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MessageNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/drafts/{draft_id}/revise", response_model=DraftReviseResponse)
async def revise_draft(
    draft_id: int,
    payload: DraftReviseRequest,
    service: DraftService = Depends(get_draft_service),
) -> DraftReviseResponse:
    try:
        return service.revise_draft(draft_id=draft_id, payload=payload)
    except DraftNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
