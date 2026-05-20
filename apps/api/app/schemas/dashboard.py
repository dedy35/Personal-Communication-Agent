from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

STATUS_VALUES = ["need_reply", "draft_ready", "waiting_reply", "fyi_only", "sensitive", "archived"]


class PlatformStatusItem(BaseModel):
    platform_account_id: int
    platform_name: str
    account_label: str
    is_active: bool
    statuses: dict[str, int]
    total_conversations: int


class PlatformStatusesResponse(BaseModel):
    items: list[PlatformStatusItem]


class ConversationItem(BaseModel):
    id: int
    platform_name: str
    title: str
    status: str
    urgency: str | None
    requires_reply: bool
    sensitive_topic_detected: bool
    contact_name: str | None
    language: str | None
    last_message_at: datetime | None
    last_message_preview: str | None


class ConversationsResponse(BaseModel):
    items: list[ConversationItem]
    total: int


class MessageItem(BaseModel):
    id: int
    conversation_id: int
    direction: str
    language: str | None
    body_original: str
    body_translated: str | None
    urgency: str | None
    requires_reply: bool
    tone: str | None
    sensitive_topic_detected: bool
    source_message_ts: datetime | None


class MessagesResponse(BaseModel):
    items: list[MessageItem]


class DraftItem(BaseModel):
    id: int
    target_conversation_id: int
    message_id: int | None
    status: str
    language: str | None
    body_original: str
    body_translated: str | None
    exact_message_body: str
    tone: str | None
    urgency: str | None
    requires_reply: bool
    sensitive_topic_detected: bool


class DraftsResponse(BaseModel):
    items: list[DraftItem]
    total: int


class DashboardCountsResponse(BaseModel):
    statuses: dict[str, int] = Field(default_factory=dict)
    total_conversations: int
    total_messages: int
    total_drafts: int
    draft_ready_count: int
    sensitive_count: int
