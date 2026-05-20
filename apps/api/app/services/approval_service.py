from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Approval, AuditLog, Conversation, Draft, Message
from app.schemas.approval import (
    ApprovalCreateRequest,
    ApprovalCreateResponse,
    SendAttemptRequest,
    SendAttemptResponse,
)


class ApprovalError(Exception):
    def __init__(self, reason_code: str, message: str) -> None:
        self.reason_code = reason_code
        self.message = message
        super().__init__(message)


class SendGuardBlockedError(ApprovalError):
    pass


@dataclass(slots=True)
class FakeSenderResult:
    fake_sender_id: str


class FakeSender:
    def send(self, conversation_id: int, body: str) -> FakeSenderResult:
        short_hash = abs(hash((conversation_id, body))) % 10_000_000
        return FakeSenderResult(fake_sender_id=f"fake-send-{conversation_id}-{short_hash}")


class ApprovalService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create_approval(self, payload: ApprovalCreateRequest) -> ApprovalCreateResponse:
        draft = self._db.get(Draft, payload.draft_id)
        if draft is None:
            self._log_audit(
                event_type="approval_blocked",
                entity_type="draft",
                entity_id=str(payload.draft_id),
                details={"reason_code": "draft_not_found"},
                exact_message_body=payload.exact_message_body,
            )
            self._db.commit()
            raise ApprovalError("draft_not_found", f"Draft {payload.draft_id} not found")

        conversation = self._db.get(Conversation, draft.target_conversation_id)
        if conversation is None:
            self._log_audit(
                event_type="approval_blocked",
                entity_type="conversation",
                entity_id=str(draft.target_conversation_id),
                details={"reason_code": "conversation_not_found"},
                exact_message_body=payload.exact_message_body,
            )
            self._db.commit()
            raise ApprovalError("conversation_not_found", f"Conversation {draft.target_conversation_id} not found")

        normalized_body = payload.exact_message_body.strip()
        if not normalized_body:
            self._log_audit(
                event_type="approval_blocked",
                entity_type="draft",
                entity_id=str(draft.id),
                details={"reason_code": "approval_missing_exact_message_body"},
            )
            self._db.commit()
            raise ApprovalError("approval_missing_exact_message_body", "exact_message_body is required")

        if payload.target_conversation_id <= 0:
            self._log_audit(
                event_type="approval_blocked",
                entity_type="draft",
                entity_id=str(draft.id),
                details={"reason_code": "approval_missing_target_conversation_id"},
                exact_message_body=normalized_body,
            )
            self._db.commit()
            raise ApprovalError("approval_missing_target_conversation_id", "target_conversation_id is required")

        if payload.target_conversation_id != draft.target_conversation_id:
            self._log_audit(
                event_type="approval_blocked",
                entity_type="draft",
                entity_id=str(draft.id),
                details={"reason_code": "approval_target_mismatch"},
                exact_message_body=normalized_body,
            )
            self._db.commit()
            raise ApprovalError("approval_target_mismatch", "target_conversation_id does not match current draft target")

        if normalized_body != draft.exact_message_body.strip():
            self._log_audit(
                event_type="approval_blocked",
                entity_type="draft",
                entity_id=str(draft.id),
                details={"reason_code": "approval_body_mismatch"},
                exact_message_body=normalized_body,
            )
            self._db.commit()
            raise ApprovalError("approval_body_mismatch", "exact_message_body does not match current draft body")

        is_group = conversation.conversation_type != "dm"
        if is_group and not payload.group_extra_confirmed:
            self._log_audit(
                event_type="approval_blocked",
                entity_type="conversation",
                entity_id=str(conversation.id),
                details={"reason_code": "group_extra_confirmation_required"},
                exact_message_body=normalized_body,
            )
            self._db.commit()
            raise ApprovalError("group_extra_confirmation_required", "group chat requires group_extra_confirmed=true")

        sensitive = conversation.sensitive_topic_detected or draft.sensitive_topic_detected
        if sensitive and not payload.sensitive_warning_acknowledged:
            self._log_audit(
                event_type="approval_blocked",
                entity_type="conversation",
                entity_id=str(conversation.id),
                details={"reason_code": "sensitive_warning_required"},
                exact_message_body=normalized_body,
            )
            self._db.commit()
            raise ApprovalError(
                "sensitive_warning_required",
                "sensitive topic requires visible warning acknowledgement before approval",
            )

        reason_suffix = payload.decision_reason or ""
        warning_flag = "warning_acknowledged=true" if payload.sensitive_warning_acknowledged else "warning_acknowledged=false"
        reason = f"{warning_flag}; {reason_suffix}".strip().strip(";")

        approval = Approval(
            draft_id=draft.id,
            approver_id=payload.approver_id,
            target_conversation_id=payload.target_conversation_id,
            exact_message_body=normalized_body,
            group_extra_confirmed=payload.group_extra_confirmed,
            decision="approved",
            sensitive_topic_detected=sensitive,
            sensitive_topic_labels=draft.sensitive_topic_labels,
            decision_reason=reason,
        )

        self._db.add(approval)
        self._log_audit(
            event_type="approval_created",
            entity_type="approval",
            entity_id=None,
            details={
                "draft_id": draft.id,
                "target_conversation_id": payload.target_conversation_id,
                "group_extra_confirmed": payload.group_extra_confirmed,
                "sensitive_warning_acknowledged": payload.sensitive_warning_acknowledged,
            },
            exact_message_body=normalized_body,
        )
        self._db.commit()
        self._db.refresh(approval)

        return ApprovalCreateResponse(
            approval_id=approval.id,
            decision=approval.decision,
            target_conversation_id=approval.target_conversation_id,
            exact_message_body=approval.exact_message_body,
            group_extra_confirmed=approval.group_extra_confirmed,
            sensitive_warning_acknowledged=payload.sensitive_warning_acknowledged,
            created_at=approval.created_at,
        )

    def _log_audit(
        self,
        *,
        event_type: str,
        entity_type: str,
        entity_id: str | None,
        details: dict[str, object] | None = None,
        exact_message_body: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_type="user",
            actor_id="owner",
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details_json=details,
            exact_message_body=exact_message_body,
        )
        self._db.add(entry)
        return entry


class SendGuardService:
    def __init__(self, db: Session, sender: FakeSender | None = None) -> None:
        self._db = db
        self._sender = sender or FakeSender()

    def attempt_send(self, payload: SendAttemptRequest) -> SendAttemptResponse:
        self._log_audit(
            event_type="send_attempted",
            entity_type="draft",
            entity_id=str(payload.draft_id),
            details={"target_conversation_id": payload.target_conversation_id},
            exact_message_body=payload.exact_message_body,
        )

        draft = self._db.get(Draft, payload.draft_id)
        if draft is None:
            return self._block_send(
                reason_code="draft_not_found",
                message=f"Draft {payload.draft_id} not found",
                payload=payload,
                entity_type="draft",
                entity_id=str(payload.draft_id),
            )

        conversation = self._db.get(Conversation, draft.target_conversation_id)
        if conversation is None:
            return self._block_send(
                reason_code="conversation_not_found",
                message=f"Conversation {draft.target_conversation_id} not found",
                payload=payload,
                entity_type="conversation",
                entity_id=str(draft.target_conversation_id),
            )

        approval = self._db.execute(
            select(Approval)
            .where(Approval.draft_id == draft.id)
            .where(Approval.decision == "approved")
            .order_by(Approval.created_at.desc(), Approval.id.desc())
            .limit(1)
        ).scalar_one_or_none()

        if approval is None:
            return self._block_send(
                reason_code="no_approval",
                message="No approved record found for this draft",
                payload=payload,
                entity_type="draft",
                entity_id=str(draft.id),
            )

        if not approval.exact_message_body.strip() or approval.target_conversation_id <= 0:
            return self._block_send(
                reason_code="approval_missing_required_fields",
                message="Approval must include exact_message_body and target_conversation_id",
                payload=payload,
                entity_type="approval",
                entity_id=str(approval.id),
            )

        if payload.target_conversation_id != draft.target_conversation_id or approval.target_conversation_id != draft.target_conversation_id:
            return self._block_send(
                reason_code="target_changed_after_approval",
                message="Target conversation changed after approval",
                payload=payload,
                entity_type="draft",
                entity_id=str(draft.id),
            )

        if payload.exact_message_body.strip() != draft.exact_message_body.strip() or approval.exact_message_body.strip() != draft.exact_message_body.strip():
            return self._block_send(
                reason_code="body_changed_after_approval",
                message="Message body changed after approval",
                payload=payload,
                entity_type="draft",
                entity_id=str(draft.id),
            )

        is_group = conversation.conversation_type != "dm"
        if is_group and not approval.group_extra_confirmed:
            return self._block_send(
                reason_code="group_extra_confirmation_required",
                message="Group chat send blocked until group_extra_confirmed=true",
                payload=payload,
                entity_type="conversation",
                entity_id=str(conversation.id),
            )

        sensitive = conversation.sensitive_topic_detected or draft.sensitive_topic_detected
        decision_reason = (approval.decision_reason or "").lower()
        if sensitive and "warning_acknowledged=true" not in decision_reason:
            return self._block_send(
                reason_code="sensitive_warning_not_acknowledged",
                message="Sensitive topic requires visible warning acknowledgement before approval",
                payload=payload,
                entity_type="approval",
                entity_id=str(approval.id),
            )

        send_result = self._sender.send(conversation_id=conversation.id, body=payload.exact_message_body.strip())

        outgoing = Message(
            conversation_id=conversation.id,
            sender_contact_id=conversation.contact_id,
            direction="outgoing",
            language=draft.language or conversation.language or "ja",
            body_original=payload.exact_message_body.strip(),
            body_translated=draft.body_translated,
            urgency=draft.urgency,
            requires_reply=False,
            tone=draft.tone,
            sensitive_topic_detected=draft.sensitive_topic_detected,
            sensitive_topic_labels=draft.sensitive_topic_labels,
        )
        self._db.add(outgoing)

        conversation.status = "waiting_reply"
        conversation.requires_reply = False

        self._log_audit(
            event_type="send_allowed_fake",
            entity_type="draft",
            entity_id=str(draft.id),
            details={
                "approval_id": approval.id,
                "target_conversation_id": conversation.id,
                "fake_sender_id": send_result.fake_sender_id,
            },
            exact_message_body=payload.exact_message_body,
        )

        self._db.commit()

        return SendAttemptResponse(
            status="sent",
            blocked=False,
            reason_code="allowed",
            message="Message sent via fake sender",
            fake_sender_id=send_result.fake_sender_id,
        )

    def _block_send(
        self,
        *,
        reason_code: str,
        message: str,
        payload: SendAttemptRequest,
        entity_type: str,
        entity_id: str | None,
    ) -> SendAttemptResponse:
        self._log_audit(
            event_type="send_blocked",
            entity_type=entity_type,
            entity_id=entity_id,
            details={"reason_code": reason_code, "target_conversation_id": payload.target_conversation_id},
            exact_message_body=payload.exact_message_body,
        )
        self._db.commit()
        return SendAttemptResponse(
            status="blocked",
            blocked=True,
            reason_code=reason_code,
            message=message,
            fake_sender_id=None,
        )

    def _log_audit(
        self,
        *,
        event_type: str,
        entity_type: str,
        entity_id: str | None,
        details: dict[str, object] | None = None,
        exact_message_body: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_type="user",
            actor_id="owner",
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details_json=details,
            exact_message_body=exact_message_body,
        )
        self._db.add(entry)
        return entry
