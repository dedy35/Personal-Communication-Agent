from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ApprovalCreateRequest(BaseModel):
    draft_id: int
    approver_id: str | None = Field(default="owner", max_length=128)
    exact_message_body: str = Field(min_length=1)
    target_conversation_id: int
    group_extra_confirmed: bool = False
    sensitive_warning_acknowledged: bool = False
    decision_reason: str | None = Field(default=None, max_length=1000)


class ApprovalCreateResponse(BaseModel):
    approval_id: int
    decision: str
    target_conversation_id: int
    exact_message_body: str
    group_extra_confirmed: bool
    sensitive_warning_acknowledged: bool
    created_at: datetime


class SendAttemptRequest(BaseModel):
    draft_id: int
    exact_message_body: str = Field(min_length=1)
    target_conversation_id: int


class SendAttemptResponse(BaseModel):
    status: str
    blocked: bool
    reason_code: str
    message: str
    fake_sender_id: str | None = None
