from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AgentChatMessage, AgentChatSession, Conversation, Draft, Message
from app.schemas.agent_chat import AgentChatMessageView, AgentChatResponse
from app.services.ai_provider import AIProvider, get_default_ai_provider


@dataclass(slots=True)
class AgentReply:
    intent: str
    text: str


class AgentResponder(Protocol):
    def generate(self, user_message: str, db: Session) -> AgentReply:
        """Return an agent response for user_message using database context."""


class RuleBasedAgentResponder:
    def generate(self, user_message: str, db: Session) -> AgentReply:
        normalized = user_message.lower().strip()

        if self._matches_urgent_today(normalized):
            return self._urgent_today(db)
        if self._matches_daily_summary(normalized):
            return self._daily_summary(db)
        if self._matches_overdue_need_reply(normalized):
            return self._older_than_24h_need_reply(db)
        if self._matches_draft_ready(normalized):
            return self._draft_ready(db)
        if self._matches_fyi_only(normalized):
            return self._fyi_only(db)

        return AgentReply(
            intent="help",
            text=(
                "I can answer these for now:\n"
                "1) urgent messages today\n"
                "2) daily narrative summary\n"
                "3) conversations older than 24h needing reply\n"
                "4) draft-ready items\n"
                "5) FYI-only items"
            ),
        )

    @staticmethod
    def _matches_urgent_today(normalized: str) -> bool:
        return ("urgent" in normalized and "today" in normalized) or "urgent messages today" in normalized

    @staticmethod
    def _matches_daily_summary(normalized: str) -> bool:
        return ("daily" in normalized and ("summary" in normalized or "narrative" in normalized or "brief" in normalized)) or (
            "ringkasan harian" in normalized
        )

    @staticmethod
    def _matches_overdue_need_reply(normalized: str) -> bool:
        return (
            ("older" in normalized and "24" in normalized and "reply" in normalized)
            or "older than 24h" in normalized
            or "overdue" in normalized
            or "lebih dari 24" in normalized
        )

    @staticmethod
    def _matches_draft_ready(normalized: str) -> bool:
        return "draft-ready" in normalized or "draft ready" in normalized or "draft" == normalized

    @staticmethod
    def _matches_fyi_only(normalized: str) -> bool:
        return "fyi" in normalized

    def _urgent_today(self, db: Session) -> AgentReply:
        now = datetime.now(tz=UTC)
        start = datetime(now.year, now.month, now.day, tzinfo=UTC)

        rows = db.execute(
            select(Conversation.title, Message.body_original, Message.urgency)
            .join(Message, Message.conversation_id == Conversation.id)
            .where(Message.direction == "incoming")
            .where(Message.requires_reply.is_(True))
            .where(Message.source_message_ts.is_not(None))
            .where(Message.source_message_ts >= start)
            .where(Message.urgency.in_(["high", "critical"]))
            .order_by(Message.source_message_ts.desc(), Message.id.desc())
            .limit(5)
        ).all()

        if not rows:
            return AgentReply(intent="urgent_today", text="No urgent incoming messages found for today.")

        lines = ["Urgent messages today:"]
        for idx, (title, body_original, urgency) in enumerate(rows, start=1):
            lines.append(f"{idx}. [{urgency}] {title}: {body_original}")
        return AgentReply(intent="urgent_today", text="\n".join(lines))

    def _daily_summary(self, db: Session) -> AgentReply:
        conversations = db.execute(select(Conversation)).scalars().all()
        drafts = db.execute(select(Draft).where(Draft.status == "draft_ready")).scalars().all()

        total = len(conversations)
        need_reply = sum(1 for item in conversations if item.status == "need_reply")
        waiting = sum(1 for item in conversations if item.status == "waiting_reply")
        sensitive = sum(1 for item in conversations if item.status == "sensitive")
        fyi_only = sum(1 for item in conversations if item.status == "fyi_only")

        summary = (
            "Daily narrative summary:\n"
            f"- Total tracked conversations: {total}\n"
            f"- Need reply: {need_reply}\n"
            f"- Waiting reply: {waiting}\n"
            f"- Sensitive: {sensitive}\n"
            f"- FYI-only: {fyi_only}\n"
            f"- Draft-ready items: {len(drafts)}"
        )
        return AgentReply(intent="daily_summary", text=summary)

    def _older_than_24h_need_reply(self, db: Session) -> AgentReply:
        threshold = datetime.now(tz=UTC) - timedelta(hours=24)

        rows = db.execute(
            select(Conversation.title, Conversation.last_message_at, Conversation.status)
            .where(Conversation.requires_reply.is_(True))
            .where(Conversation.last_message_at.is_not(None))
            .where(Conversation.last_message_at <= threshold)
            .where(Conversation.status.in_(["need_reply", "sensitive"]))
            .order_by(Conversation.last_message_at.asc(), Conversation.id.asc())
            .limit(10)
        ).all()

        if not rows:
            return AgentReply(intent="older_24h_need_reply", text="No conversations older than 24h that still need a reply.")

        lines = ["Conversations older than 24h needing reply:"]
        for idx, (title, last_message_at, status) in enumerate(rows, start=1):
            timestamp = last_message_at.isoformat() if last_message_at else "unknown"
            lines.append(f"{idx}. [{status}] {title} (last message: {timestamp})")

        return AgentReply(intent="older_24h_need_reply", text="\n".join(lines))

    def _draft_ready(self, db: Session) -> AgentReply:
        rows = db.execute(
            select(Draft.id, Draft.target_conversation_id, Draft.exact_message_body)
            .where(Draft.status == "draft_ready")
            .order_by(Draft.updated_at.desc(), Draft.id.desc())
            .limit(10)
        ).all()

        if not rows:
            return AgentReply(intent="draft_ready", text="No draft-ready items at the moment.")

        lines = ["Draft-ready items:"]
        for draft_id, conversation_id, exact_message_body in rows:
            lines.append(f"- Draft #{draft_id} for conversation #{conversation_id}: {exact_message_body}")

        return AgentReply(intent="draft_ready", text="\n".join(lines))

    def _fyi_only(self, db: Session) -> AgentReply:
        rows = db.execute(
            select(Conversation.title, Conversation.urgency)
            .where(Conversation.status == "fyi_only")
            .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.id.desc())
            .limit(10)
        ).all()

        if not rows:
            return AgentReply(intent="fyi_only", text="No FYI-only conversations found.")

        lines = ["FYI-only items:"]
        for idx, (title, urgency) in enumerate(rows, start=1):
            lines.append(f"{idx}. {title} (urgency: {urgency or 'none'})")

        return AgentReply(intent="fyi_only", text="\n".join(lines))


class AgentService:
    def __init__(
        self,
        db: Session,
        responder: AgentResponder | None = None,
        ai_provider: AIProvider | None = None,
    ) -> None:
        self._db = db
        self._responder = responder or RuleBasedAgentResponder()
        self._ai_provider = ai_provider or get_default_ai_provider()

    def chat(self, message: str, session_key: str | None, language: str | None = None) -> AgentChatResponse:
        session = self._get_or_create_session(session_key=session_key)

        user_message = AgentChatMessage(
            session_id=session.id,
            role="user",
            body=message,
            language=language,
        )
        self._db.add(user_message)

        agent_reply = self._responder.generate(user_message=message, db=self._db)

        final_reply = self._refine_reply_with_ai(
            intent=agent_reply.intent,
            user_message=message,
            fallback_reply=agent_reply.text,
        )

        assistant_message = AgentChatMessage(
            session_id=session.id,
            role="assistant",
            body=final_reply,
            language="en",
        )
        self._db.add(assistant_message)

        self._db.commit()

        rows = self._db.execute(
            select(AgentChatMessage)
            .where(AgentChatMessage.session_id == session.id)
            .order_by(AgentChatMessage.created_at.asc(), AgentChatMessage.id.asc())
            .limit(100)
        ).scalars().all()

        return AgentChatResponse(
            session_key=session.session_key,
            matched_intent=agent_reply.intent,
            reply=final_reply,
            messages=[
                AgentChatMessageView(
                    role=item.role,
                    body=item.body,
                    language=item.language,
                    created_at=item.created_at,
                )
                for item in rows
            ],
        )

    def _refine_reply_with_ai(self, *, intent: str, user_message: str, fallback_reply: str) -> str:
        if not self._ai_provider.is_available():
            return fallback_reply

        prompt = (
            "Refine this operational assistant response.\n"
            f"Intent: {intent}\n"
            f"User request: {user_message}\n"
            f"Draft response:\n{fallback_reply}\n\n"
            "Keep all facts and counts exactly the same. Improve clarity only."
        )
        try:
            refined = self._ai_provider.generate_text(
                system_prompt=(
                    "You are a concise assistant for communication operations. "
                    "Do not invent facts or numbers."
                ),
                user_prompt=prompt,
                temperature=0.1,
            )
        except Exception:
            return fallback_reply

        if not refined:
            return fallback_reply
        return refined.strip() or fallback_reply

    def _get_or_create_session(self, session_key: str | None) -> AgentChatSession:
        if session_key:
            existing = self._db.execute(
                select(AgentChatSession).where(AgentChatSession.session_key == session_key)
            ).scalar_one_or_none()
            if existing is not None:
                return existing

        generated = session_key or f"chat-{uuid4().hex[:12]}"
        session = AgentChatSession(session_key=generated, title="Agent Chat", status="active")
        self._db.add(session)
        self._db.flush()
        return session
