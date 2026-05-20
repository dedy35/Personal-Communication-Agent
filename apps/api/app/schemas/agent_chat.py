from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_key: str | None = Field(default=None, max_length=128)
    language: str | None = Field(default=None, max_length=16)


class AgentChatMessageView(BaseModel):
    role: str
    body: str
    language: str | None = None
    created_at: datetime


class AgentChatResponse(BaseModel):
    session_key: str
    matched_intent: str
    reply: str
    messages: list[AgentChatMessageView]
