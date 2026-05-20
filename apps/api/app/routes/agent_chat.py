from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.schemas.agent_chat import AgentChatRequest, AgentChatResponse
from app.services.agent_service import AgentService

router = APIRouter(tags=["agent"])


async def get_agent_service(db: Session = Depends(get_db_session)) -> AgentService:
    return AgentService(db=db)


@router.post("/agent/chat", response_model=AgentChatResponse)
async def agent_chat(
    payload: AgentChatRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentChatResponse:
    return service.chat(message=payload.message, session_key=payload.session_key, language=payload.language)
