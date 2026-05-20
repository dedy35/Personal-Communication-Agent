from __future__ import annotations

from pydantic import BaseModel, Field


class TranslationContext(BaseModel):
    relationship_type: str | None = Field(default=None)
    conversation_type: str | None = Field(default=None)
    platform_name: str | None = Field(default=None)


class TranslationAnalysis(BaseModel):
    detected_language: str
    body_original: str
    body_translated: str
    practical_meaning: str
    tone: str
    hierarchy: str
    urgency: str
    risk_explanation: str
