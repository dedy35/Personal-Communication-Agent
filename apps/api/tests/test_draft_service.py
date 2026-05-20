from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base, Contact, Conversation, Message, PlatformAccount
from app.schemas.drafting import DraftGenerateRequest, DraftReviseRequest, DraftTone
from app.services.draft_service import DraftService


def _create_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return factory()


def _seed_conversation(session: Session) -> tuple[int, int]:
    account = PlatformAccount(platform_name="line", account_label="LINE JP", is_active=True)
    contact = Contact(
        platform_account=account,
        display_name="Takahashi-san",
        relationship_type="senior",
        preferred_language="ja",
        preferred_tone="business_formal",
    )
    conversation = Conversation(
        platform_account=account,
        contact=contact,
        title="Ticket 1580 Follow-up",
        language="ja",
        status="need_reply",
        urgency="high",
        requires_reply=True,
        last_message_at=datetime.now(tz=UTC),
    )
    message = Message(
        conversation=conversation,
        sender_contact=contact,
        direction="incoming",
        language="ja",
        body_original="本日中に確認してご報告いただけますか。",
        body_translated="Bisakah Anda cek dan melaporkan hari ini?",
        urgency="high",
        requires_reply=True,
        tone="polite_formal",
        source_message_ts=datetime.now(tz=UTC),
    )

    session.add_all([account, contact, conversation, message])
    session.commit()
    session.refresh(conversation)
    session.refresh(message)

    return conversation.id, message.id


def test_generate_draft_business_formal() -> None:
    session = _create_session()
    conversation_id, message_id = _seed_conversation(session)

    service = DraftService(db=session)
    result = service.generate_draft(
        DraftGenerateRequest(
            conversation_id=conversation_id,
            source_message_id=message_id,
            selected_tone=DraftTone.BUSINESS_FORMAL,
        )
    )

    assert result.draft.id > 0
    assert result.draft.tone == DraftTone.BUSINESS_FORMAL.value
    assert "承知" in result.draft.body_original
    assert result.used_context["relationship_type"] == "senior"


def test_revise_draft_with_natural_language_instruction() -> None:
    session = _create_session()
    conversation_id, message_id = _seed_conversation(session)

    service = DraftService(db=session)
    generated = service.generate_draft(
        DraftGenerateRequest(
            conversation_id=conversation_id,
            source_message_id=message_id,
            selected_tone=DraftTone.PROFESSIONAL_CONCISE,
        )
    )

    revised = service.revise_draft(
        draft_id=generated.draft.id,
        payload=DraftReviseRequest(
            instruction="make it shorter, add this context: 進捗は本日18時までに共有します, make it more polite"
        ),
    )

    assert revised.draft.id == generated.draft.id
    assert len(revised.draft.applied_actions) >= 2
    assert "進捗は本日18時までに共有します" in revised.draft.body_original
    assert "恐れ入りますが" in revised.draft.body_original or "よろしくお願いいたします" in revised.draft.body_original
