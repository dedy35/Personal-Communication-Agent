from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class PlatformAccount(TimestampMixin, Base):
    __tablename__ = "platform_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform_name: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    account_label: Mapped[str] = mapped_column(String(120), nullable=False)
    external_account_id: Mapped[str | None] = mapped_column(String(191), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    metadata_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)

    contacts: Mapped[list[Contact]] = relationship(back_populates="platform_account")
    conversations: Mapped[list[Conversation]] = relationship(back_populates="platform_account")


class Contact(TimestampMixin, Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform_account_id: Mapped[int] = mapped_column(ForeignKey("platform_accounts.id", ondelete="CASCADE"), nullable=False)
    external_contact_id: Mapped[str | None] = mapped_column(String(191), nullable=True)
    display_name: Mapped[str] = mapped_column(String(191), nullable=False)
    handle: Mapped[str | None] = mapped_column(String(191), nullable=True)
    relationship_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    preferred_language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    preferred_tone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sensitive_topic_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    sensitive_topic_labels: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    platform_account: Mapped[PlatformAccount] = relationship(back_populates="contacts")
    conversations: Mapped[list[Conversation]] = relationship(back_populates="contact")
