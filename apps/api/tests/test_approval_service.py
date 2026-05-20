from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.models import Approval, AuditLog, Base, Contact, Conversation, Draft, Message, PlatformAccount
from app.schemas.approval import ApprovalCreateRequest, SendAttemptRequest
from app.services.approval_service import ApprovalService, SendGuardService


def _create_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return factory()


def _seed_base(
    session: Session,
    *,
    conversation_type: str = "dm",
    sensitive: bool = False,
) -> tuple[int, int, int]:
    account = PlatformAccount(platform_name="slack", account_label="Work Slack", is_active=True)
    contact = Contact(platform_account=account, display_name="Takahashi-san", relationship_type="senior")
    conversation = Conversation(
        platform_account=account,
        contact=contact,
        title="Ticket 1580",
        conversation_type=conversation_type,
        language="ja",
        status="need_reply",
        urgency="high",
        requires_reply=True,
        sensitive_topic_detected=sensitive,
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
        source_message_ts=datetime.now(tz=UTC),
    )

    session.add_all([account, contact, conversation, message])
    session.flush()

    draft = Draft(
        message_id=message.id,
        target_conversation_id=conversation.id,
        language="ja",
        body_original="承知いたしました。確認のうえ、ご連絡いたします。",
        body_translated="Baik, saya akan cek dan mengabari.",
        exact_message_body="承知いたしました。確認のうえ、ご連絡いたします。",
        tone="business_formal",
        urgency="high",
        requires_reply=True,
        status="draft_ready",
        sensitive_topic_detected=sensitive,
    )
    session.add(draft)
    session.commit()
    session.refresh(conversation)
    session.refresh(message)
    session.refresh(draft)

    return conversation.id, message.id, draft.id


def _create_approval(
    session: Session,
    draft_id: int,
    conversation_id: int,
    *,
    group_extra_confirmed: bool = True,
    warning_ack: bool = True,
    exact_message_body: str = "承知いたしました。確認のうえ、ご連絡いたします。",
    target_conversation_id: int | None = None,
    decision_reason: str | None = None,
) -> Approval:
    service = ApprovalService(db=session)
    result = service.create_approval(
        ApprovalCreateRequest(
            draft_id=draft_id,
            approver_id="owner",
            exact_message_body=exact_message_body,
            target_conversation_id=target_conversation_id or conversation_id,
            group_extra_confirmed=group_extra_confirmed,
            sensitive_warning_acknowledged=warning_ack,
            decision_reason=decision_reason,
        )
    )
    approval = session.get(Approval, result.approval_id)
    assert approval is not None
    return approval


def test_block_send_without_approval_and_audit_logged() -> None:
    session = _create_session()
    conversation_id, _, draft_id = _seed_base(session)

    guard = SendGuardService(db=session)
    response = guard.attempt_send(
        SendAttemptRequest(
            draft_id=draft_id,
            exact_message_body="承知いたしました。確認のうえ、ご連絡いたします。",
            target_conversation_id=conversation_id,
        )
    )

    assert response.blocked is True
    assert response.reason_code == "no_approval"

    blocked_events = session.execute(
        select(AuditLog).where(AuditLog.event_type == "send_blocked").order_by(AuditLog.id.desc())
    ).scalars().all()
    assert blocked_events
    assert blocked_events[0].details_json is not None
    assert blocked_events[0].details_json.get("reason_code") == "no_approval"


def test_block_send_when_approval_missing_required_fields() -> None:
    session = _create_session()
    conversation_id, _, draft_id = _seed_base(session)

    bad_approval = Approval(
        draft_id=draft_id,
        approver_id="owner",
        target_conversation_id=conversation_id,
        exact_message_body=" ",
        group_extra_confirmed=True,
        decision="approved",
        decision_reason="warning_acknowledged=true",
    )
    session.add(bad_approval)
    session.commit()

    guard = SendGuardService(db=session)
    response = guard.attempt_send(
        SendAttemptRequest(
            draft_id=draft_id,
            exact_message_body="承知いたしました。確認のうえ、ご連絡いたします。",
            target_conversation_id=conversation_id,
        )
    )

    assert response.blocked is True
    assert response.reason_code == "approval_missing_required_fields"


def test_block_send_when_body_changed_after_approval() -> None:
    session = _create_session()
    conversation_id, _, draft_id = _seed_base(session)

    draft = session.get(Draft, draft_id)
    assert draft is not None

    _create_approval(
        session,
        draft_id=draft_id,
        conversation_id=conversation_id,
        exact_message_body=draft.exact_message_body,
    )

    draft.exact_message_body = "変更後の本文です。"
    session.commit()

    guard = SendGuardService(db=session)
    response = guard.attempt_send(
        SendAttemptRequest(
            draft_id=draft_id,
            exact_message_body="承知いたしました。確認のうえ、ご連絡いたします。",
            target_conversation_id=conversation_id,
        )
    )

    assert response.blocked is True
    assert response.reason_code == "body_changed_after_approval"


def test_block_send_when_target_changed_after_approval() -> None:
    session = _create_session()
    conversation_id, _, draft_id = _seed_base(session)

    _create_approval(session, draft_id=draft_id, conversation_id=conversation_id)

    account = PlatformAccount(platform_name="line", account_label="Alt", is_active=True)
    contact = Contact(platform_account=account, display_name="Alt Contact")
    alt_conversation = Conversation(
        platform_account=account,
        contact=contact,
        title="Alt Conversation",
        conversation_type="dm",
        language="ja",
        status="need_reply",
        urgency="medium",
        requires_reply=True,
    )
    session.add_all([account, contact, alt_conversation])
    session.flush()

    draft = session.get(Draft, draft_id)
    assert draft is not None
    draft.target_conversation_id = alt_conversation.id
    session.commit()

    guard = SendGuardService(db=session)
    response = guard.attempt_send(
        SendAttemptRequest(
            draft_id=draft_id,
            exact_message_body="承知いたしました。確認のうえ、ご連絡いたします。",
            target_conversation_id=conversation_id,
        )
    )

    assert response.blocked is True
    assert response.reason_code == "target_changed_after_approval"


def test_block_send_for_group_without_group_extra_confirmed() -> None:
    session = _create_session()
    conversation_id, _, draft_id = _seed_base(session, conversation_type="group", sensitive=False)

    bad_approval = Approval(
        draft_id=draft_id,
        approver_id="owner",
        target_conversation_id=conversation_id,
        exact_message_body="承知いたしました。確認のうえ、ご連絡いたします。",
        group_extra_confirmed=False,
        decision="approved",
        decision_reason="warning_acknowledged=true",
    )
    session.add(bad_approval)
    session.commit()

    guard = SendGuardService(db=session)
    response = guard.attempt_send(
        SendAttemptRequest(
            draft_id=draft_id,
            exact_message_body="承知いたしました。確認のうえ、ご連絡いたします。",
            target_conversation_id=conversation_id,
        )
    )

    assert response.blocked is True
    assert response.reason_code == "group_extra_confirmation_required"


def test_block_approval_for_sensitive_topic_without_warning() -> None:
    session = _create_session()
    conversation_id, _, draft_id = _seed_base(session, conversation_type="dm", sensitive=True)

    service = ApprovalService(db=session)

    try:
        service.create_approval(
            ApprovalCreateRequest(
                draft_id=draft_id,
                approver_id="owner",
                exact_message_body="承知いたしました。確認のうえ、ご連絡いたします。",
                target_conversation_id=conversation_id,
                group_extra_confirmed=True,
                sensitive_warning_acknowledged=False,
            )
        )
    except Exception as exc:
        assert getattr(exc, "reason_code", None) == "sensitive_warning_required"
    else:
        raise AssertionError("Expected sensitive_warning_required block")

    blocked_events = session.execute(
        select(AuditLog).where(AuditLog.event_type == "approval_blocked").order_by(AuditLog.id.desc())
    ).scalars().all()
    assert blocked_events
    assert blocked_events[0].details_json is not None
    assert blocked_events[0].details_json.get("reason_code") == "sensitive_warning_required"
