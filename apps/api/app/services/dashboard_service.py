from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Contact, Conversation, Draft, Message, PlatformAccount
from app.schemas.dashboard import (
    STATUS_VALUES,
    ConversationItem,
    DashboardCountsResponse,
    DraftItem,
    MessageItem,
    PlatformStatusItem,
)


class DashboardService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_platform_statuses(self) -> list[PlatformStatusItem]:
        accounts = self._db.execute(select(PlatformAccount).order_by(PlatformAccount.id.asc())).scalars().all()

        items: list[PlatformStatusItem] = []
        for account in accounts:
            rows = self._db.execute(
                select(Conversation.status, func.count(Conversation.id))
                .where(Conversation.platform_account_id == account.id)
                .group_by(Conversation.status)
            ).all()

            statuses = {status: 0 for status in STATUS_VALUES}
            total = 0
            for status, count in rows:
                statuses[status] = int(count)
                total += int(count)

            items.append(
                PlatformStatusItem(
                    platform_account_id=account.id,
                    platform_name=account.platform_name,
                    account_label=account.account_label,
                    is_active=account.is_active,
                    statuses=statuses,
                    total_conversations=total,
                )
            )

        return items

    def list_conversations(
        self,
        platform: str | None,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[ConversationItem], int]:
        filters = []
        if platform:
            filters.append(PlatformAccount.platform_name == platform)
        if status:
            filters.append(Conversation.status == status)

        base_stmt = (
            select(Conversation, PlatformAccount.platform_name, Contact.display_name)
            .join(PlatformAccount, PlatformAccount.id == Conversation.platform_account_id)
            .outerjoin(Contact, Contact.id == Conversation.contact_id)
            .where(*filters)
        )

        total = int(
            self._db.execute(
                select(func.count())
                .select_from(Conversation)
                .join(PlatformAccount, PlatformAccount.id == Conversation.platform_account_id)
                .where(*filters)
            ).scalar_one()
        )

        rows = self._db.execute(
            base_stmt.order_by(Conversation.last_message_at.desc().nullslast(), Conversation.id.desc()).limit(limit).offset(offset)
        ).all()

        items: list[ConversationItem] = []
        for conversation, platform_name, contact_name in rows:
            last_message_preview = self._db.execute(
                select(Message.body_original)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.source_message_ts.desc().nullslast(), Message.id.desc())
                .limit(1)
            ).scalar_one_or_none()

            items.append(
                ConversationItem(
                    id=conversation.id,
                    platform_name=platform_name,
                    title=conversation.title,
                    status=conversation.status,
                    urgency=conversation.urgency,
                    requires_reply=conversation.requires_reply,
                    sensitive_topic_detected=conversation.sensitive_topic_detected,
                    contact_name=contact_name,
                    language=conversation.language,
                    last_message_at=conversation.last_message_at,
                    last_message_preview=last_message_preview,
                )
            )

        return items, total

    def list_messages(self, conversation_id: int, limit: int) -> list[MessageItem]:
        rows = self._db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.source_message_ts.asc().nullsfirst(), Message.id.asc())
            .limit(limit)
        ).scalars().all()

        return [
            MessageItem(
                id=row.id,
                conversation_id=row.conversation_id,
                direction=row.direction,
                language=row.language,
                body_original=row.body_original,
                body_translated=row.body_translated,
                urgency=row.urgency,
                requires_reply=row.requires_reply,
                tone=row.tone,
                sensitive_topic_detected=row.sensitive_topic_detected,
                source_message_ts=row.source_message_ts,
            )
            for row in rows
        ]

    def list_drafts(self, status: str | None, limit: int, offset: int) -> tuple[list[DraftItem], int]:
        base_stmt = select(Draft)
        if status:
            base_stmt = base_stmt.where(Draft.status == status)

        total = int(self._db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one())

        rows = self._db.execute(
            base_stmt.order_by(Draft.updated_at.desc(), Draft.id.desc()).limit(limit).offset(offset)
        ).scalars().all()

        items = [
            DraftItem(
                id=row.id,
                target_conversation_id=row.target_conversation_id,
                message_id=row.message_id,
                status=row.status,
                language=row.language,
                body_original=row.body_original,
                body_translated=row.body_translated,
                exact_message_body=row.exact_message_body,
                tone=row.tone,
                urgency=row.urgency,
                requires_reply=row.requires_reply,
                sensitive_topic_detected=row.sensitive_topic_detected,
            )
            for row in rows
        ]
        return items, total

    def get_dashboard_counts(self) -> DashboardCountsResponse:
        statuses = {status: 0 for status in STATUS_VALUES}
        status_rows = self._db.execute(select(Conversation.status, func.count(Conversation.id)).group_by(Conversation.status)).all()
        for status, count in status_rows:
            statuses[status] = int(count)

        total_conversations = int(self._db.execute(select(func.count(Conversation.id))).scalar_one())
        total_messages = int(self._db.execute(select(func.count(Message.id))).scalar_one())
        total_drafts = int(self._db.execute(select(func.count(Draft.id))).scalar_one())
        draft_ready_count = int(
            self._db.execute(select(func.count(Draft.id)).where(Draft.status == "draft_ready")).scalar_one()
        )
        sensitive_count = int(
            self._db.execute(
                select(func.count(Conversation.id)).where(
                    (Conversation.status == "sensitive") | (Conversation.sensitive_topic_detected.is_(True))
                )
            ).scalar_one()
        )

        return DashboardCountsResponse(
            statuses=statuses,
            total_conversations=total_conversations,
            total_messages=total_messages,
            total_drafts=total_drafts,
            draft_ready_count=draft_ready_count,
            sensitive_count=sensitive_count,
        )
