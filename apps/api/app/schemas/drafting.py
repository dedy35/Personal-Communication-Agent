from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DraftTone(str, Enum):
    BUSINESS_FORMAL = "business_formal"
    PROFESSIONAL_CONCISE = "professional_concise"
    FRIENDLY_POLITE = "friendly_polite"
    APOLOGY = "apology"
    DELAY_RESPONSE = "delay_response"
    CLARIFICATION = "clarification"


class TranslationAnalysisInput(BaseModel):
    detected_language: str | None = None
    body_translated: str | None = None
    practical_meaning: str | None = None
    tone: str | None = None
    hierarchy: str | None = None
    urgency: str | None = None
    risk_explanation: str | None = None


class DraftGenerateRequest(BaseModel):
    conversation_id: int
    source_message_id: int | None = None
    selected_tone: DraftTone
    urgency_override: str | None = Field(default=None, max_length=16)
    additional_context: str | None = Field(default=None, max_length=1000)
    translation_analysis: TranslationAnalysisInput | None = None


class DraftReviseRequest(BaseModel):
    instruction: str = Field(min_length=1, max_length=2000)
    selected_tone: DraftTone | None = None


class DraftView(BaseModel):
    id: int
    target_conversation_id: int
    message_id: int | None
    status: str
    tone: str | None
    urgency: str | None
    body_original: str
    body_translated: str | None
    exact_message_body: str
    applied_actions: list[str] = Field(default_factory=list)
    updated_at: datetime


class DraftGenerateResponse(BaseModel):
    draft: DraftView
    used_context: dict[str, str | None]


class DraftReviseResponse(BaseModel):
    draft: DraftView
