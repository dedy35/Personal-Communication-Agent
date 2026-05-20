from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.schemas.approval import (
    ApprovalCreateRequest,
    ApprovalCreateResponse,
    SendAttemptRequest,
    SendAttemptResponse,
)
from app.services.approval_service import ApprovalError, ApprovalService, SendGuardService

router = APIRouter(tags=["approval"])


async def get_approval_service(db: Session = Depends(get_db_session)) -> ApprovalService:
    return ApprovalService(db=db)


async def get_send_guard_service(db: Session = Depends(get_db_session)) -> SendGuardService:
    return SendGuardService(db=db)


@router.post("/approvals", response_model=ApprovalCreateResponse)
async def create_approval(
    payload: ApprovalCreateRequest,
    service: ApprovalService = Depends(get_approval_service),
) -> ApprovalCreateResponse:
    try:
        return service.create_approval(payload)
    except ApprovalError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"reason_code": exc.reason_code, "message": exc.message},
        ) from exc


@router.post("/send/attempt", response_model=SendAttemptResponse)
async def attempt_send(
    payload: SendAttemptRequest,
    service: SendGuardService = Depends(get_send_guard_service),
) -> SendAttemptResponse:
    return service.attempt_send(payload)
