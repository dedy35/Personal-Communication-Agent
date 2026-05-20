from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class Draft(TimestampMixin, Base):
    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    target_conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    body_original: Mapped[str] = mapped_column(Text, nullable=False)
    body_translated: Mapped[str | None] = mapped_column(Text, nullable=True)
    exact_message_body: Mapped[str] = mapped_column(Text, nullable=False)
    tone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    urgency: Mapped[str | None] = mapped_column(String(16), nullable=True)
    requires_reply: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft_ready", server_default="draft_ready")
    sensitive_topic_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    sensitive_topic_labels: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    target_conversation: Mapped[Conversation] = relationship(back_populates="drafts")
    approvals: Mapped[list[Approval]] = relationship(back_populates="draft")


class Approval(TimestampMixin, Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("drafts.id", ondelete="CASCADE"), nullable=False, index=True)
    approver_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    target_conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    exact_message_body: Mapped[str] = mapped_column(Text, nullable=False)
    group_extra_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    decision: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending")
    sensitive_topic_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    sensitive_topic_labels: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    draft: Mapped[Draft] = relationship(back_populates="approvals")
    target_conversation: Mapped[Conversation] = relationship(back_populates="approvals")
