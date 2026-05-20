from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.drafting import Approval, Draft
    from app.models.platform import Contact, PlatformAccount


class Conversation(TimestampMixin, Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform_account_id: Mapped[int] = mapped_column(ForeignKey("platform_accounts.id", ondelete="CASCADE"), nullable=False)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    external_conversation_id: Mapped[str | None] = mapped_column(String(191), nullable=True)
    conversation_type: Mapped[str] = mapped_column(String(32), nullable=False, default="dm", server_default="dm")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="need_reply", server_default="need_reply")
    urgency: Mapped[str | None] = mapped_column(String(16), nullable=True)
    requires_reply: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    sensitive_topic_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    sensitive_topic_labels: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    platform_account: Mapped[PlatformAccount] = relationship(back_populates="conversations")
    contact: Mapped[Contact | None] = relationship(back_populates="conversations")
    messages: Mapped[list[Message]] = relationship(back_populates="conversation")
    summaries: Mapped[list[ConversationSummary]] = relationship(back_populates="conversation")
    drafts: Mapped[list[Draft]] = relationship(back_populates="target_conversation")
    approvals: Mapped[list[Approval]] = relationship(back_populates="target_conversation")


class Message(TimestampMixin, Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    body_original: Mapped[str] = mapped_column(Text, nullable=False)
    body_translated: Mapped[str | None] = mapped_column(Text, nullable=True)
    urgency: Mapped[str | None] = mapped_column(String(16), nullable=True)
    requires_reply: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    tone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sensitive_topic_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    sensitive_topic_labels: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    source_message_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    sender_contact: Mapped[Contact | None] = relationship()


class ConversationSummary(TimestampMixin, Base):
    __tablename__ = "conversation_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    key_points: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    urgency: Mapped[str | None] = mapped_column(String(16), nullable=True)
    requires_reply: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    sensitive_topic_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    sensitive_topic_labels: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    conversation: Mapped[Conversation] = relationship(back_populates="summaries")
