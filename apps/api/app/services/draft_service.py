from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Conversation, Draft, Message
from app.schemas.drafting import (
    DraftGenerateRequest,
    DraftGenerateResponse,
    DraftReviseRequest,
    DraftReviseResponse,
    DraftTone,
    DraftView,
    TranslationAnalysisInput,
)
from app.schemas.translation import TranslationContext
from app.services.translation_service import TranslationService

if TYPE_CHECKING:
    from app.schemas.translation import TranslationAnalysis


class ConversationNotFoundError(Exception):
    pass


class MessageNotFoundError(Exception):
    pass


class DraftNotFoundError(Exception):
    pass


@dataclass(slots=True)
class _DraftPlan:
    japanese_text: str
    tone: str
    urgency: str


class DraftService:
    """Generate and revise draft replies.

    Designed to be deterministic and testable now, with clear extension points
    for model-based generation later.
    """

    def __init__(self, db: Session, translation_service: TranslationService | None = None) -> None:
        self._db = db
        self._translation_service = translation_service or TranslationService()

    def generate_draft(self, payload: DraftGenerateRequest) -> DraftGenerateResponse:
        conversation = self._db.get(Conversation, payload.conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(f"Conversation {payload.conversation_id} not found")

        source_message = self._resolve_source_message(conversation_id=conversation.id, source_message_id=payload.source_message_id)

        context = TranslationContext(
            relationship_type=conversation.contact.relationship_type if conversation.contact else None,
            conversation_type=conversation.conversation_type,
            platform_name=conversation.platform_account.platform_name if conversation.platform_account else None,
        )

        analysis = self._resolve_translation_analysis(
            source_text=source_message.body_original,
            provided=payload.translation_analysis,
            context=context,
        )

        urgency = payload.urgency_override or analysis.urgency or source_message.urgency or conversation.urgency or "medium"

        plan = self._build_japanese_draft(
            tone=payload.selected_tone,
            urgency=urgency,
            practical_meaning=analysis.practical_meaning,
            source_text=source_message.body_original,
            additional_context=payload.additional_context,
        )

        translated = self._translation_service.translate_to_indonesian(plan.japanese_text)

        draft = Draft(
            message_id=source_message.id,
            target_conversation_id=conversation.id,
            language="ja",
            body_original=plan.japanese_text,
            body_translated=translated,
            exact_message_body=plan.japanese_text,
            tone=plan.tone,
            urgency=plan.urgency,
            requires_reply=True,
            status="draft_ready",
            sensitive_topic_detected=conversation.sensitive_topic_detected or source_message.sensitive_topic_detected,
            sensitive_topic_labels=conversation.sensitive_topic_labels or source_message.sensitive_topic_labels,
        )

        self._db.add(draft)

        if conversation.status in {"need_reply", "waiting_reply", "sensitive"}:
            conversation.status = "draft_ready"

        self._db.commit()
        self._db.refresh(draft)

        used_context = {
            "conversation_title": conversation.title,
            "contact_name": conversation.contact.display_name if conversation.contact else None,
            "relationship_type": conversation.contact.relationship_type if conversation.contact else None,
            "platform_name": conversation.platform_account.platform_name if conversation.platform_account else None,
            "selected_tone": payload.selected_tone.value,
            "urgency": plan.urgency,
            "practical_meaning": analysis.practical_meaning,
        }

        return DraftGenerateResponse(draft=self._to_view(draft), used_context=used_context)

    def revise_draft(self, draft_id: int, payload: DraftReviseRequest) -> DraftReviseResponse:
        draft = self._db.get(Draft, draft_id)
        if draft is None:
            raise DraftNotFoundError(f"Draft {draft_id} not found")

        base_text = draft.exact_message_body
        applied_actions: list[str] = []

        if payload.selected_tone is not None:
            base_text, tone_action = self._retone(base_text, payload.selected_tone)
            applied_actions.append(tone_action)

        revised_text, revision_actions = self._apply_instruction(base_text, payload.instruction)
        applied_actions.extend(revision_actions)

        draft.body_original = revised_text
        draft.exact_message_body = revised_text
        draft.body_translated = self._translation_service.translate_to_indonesian(revised_text)
        if payload.selected_tone is not None:
            draft.tone = payload.selected_tone.value

        self._db.commit()
        self._db.refresh(draft)

        view = self._to_view(draft)
        view.applied_actions = applied_actions
        return DraftReviseResponse(draft=view)

    def _resolve_source_message(self, conversation_id: int, source_message_id: int | None) -> Message:
        if source_message_id is not None:
            message = self._db.get(Message, source_message_id)
            if message is None or message.conversation_id != conversation_id:
                raise MessageNotFoundError(f"Message {source_message_id} not found in conversation {conversation_id}")
            return message

        message = self._db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.source_message_ts.desc().nullslast(), Message.id.desc())
            .limit(1)
        ).scalar_one_or_none()

        if message is None:
            raise MessageNotFoundError(f"No messages found for conversation {conversation_id}")

        return message

    def _resolve_translation_analysis(
        self,
        *,
        source_text: str,
        provided: TranslationAnalysisInput | None,
        context: TranslationContext,
    ) -> TranslationAnalysis:
        if provided is None:
            return self._translation_service.analyze_message(source_text, context=context)

        base = self._translation_service.analyze_message(source_text, context=context)

        return base.model_copy(
            update={
                "detected_language": provided.detected_language or base.detected_language,
                "body_translated": provided.body_translated or base.body_translated,
                "practical_meaning": provided.practical_meaning or base.practical_meaning,
                "tone": provided.tone or base.tone,
                "hierarchy": provided.hierarchy or base.hierarchy,
                "urgency": provided.urgency or base.urgency,
                "risk_explanation": provided.risk_explanation or base.risk_explanation,
            }
        )

    def _build_japanese_draft(
        self,
        *,
        tone: DraftTone,
        urgency: str,
        practical_meaning: str,
        source_text: str,
        additional_context: str | None,
    ) -> _DraftPlan:
        action = self._infer_action(practical_meaning=practical_meaning, source_text=source_text, urgency=urgency)
        context_snippet = f" {additional_context.strip()}" if additional_context and additional_context.strip() else ""

        if tone == DraftTone.BUSINESS_FORMAL:
            text = f"承知いたしました。{action}。必要事項は改めてご報告いたします。{context_snippet}".strip()
        elif tone == DraftTone.PROFESSIONAL_CONCISE:
            text = f"承知しました。{action}。{context_snippet}".strip()
        elif tone == DraftTone.FRIENDLY_POLITE:
            text = f"ご連絡ありがとうございます。{action}。よろしくお願いします。{context_snippet}".strip()
        elif tone == DraftTone.APOLOGY:
            text = f"ご連絡ありがとうございます。返信が遅くなり申し訳ありません。{action}。{context_snippet}".strip()
        elif tone == DraftTone.DELAY_RESPONSE:
            text = f"ご連絡ありがとうございます。確認に少しお時間をいただけますと幸いです。{action}。{context_snippet}".strip()
        else:  # DraftTone.CLARIFICATION
            clarification = self._build_clarification(source_text)
            text = f"ご連絡ありがとうございます。認識を合わせるため、{clarification}。{context_snippet}".strip()

        text = re.sub(r"\s+", " ", text).strip()
        return _DraftPlan(japanese_text=text, tone=tone.value, urgency=urgency)

    @staticmethod
    def _infer_action(*, practical_meaning: str, source_text: str, urgency: str) -> str:
        combined = f"{practical_meaning} {source_text}".lower()

        if "deadline" in combined or "納期" in source_text:
            return "明日までに確定可否をご連絡いたします"
        if "confirm" in combined or "確認" in source_text:
            if urgency == "high":
                return "優先して確認し、本日中にご連絡いたします"
            return "確認のうえ、ご連絡いたします"
        if "report" in combined or "報告" in source_text:
            return "確認後、速やかにご報告いたします"

        if urgency == "high":
            return "優先度高く対応し、進捗をご連絡いたします"
        return "内容を確認し、順次対応いたします"

    @staticmethod
    def _build_clarification(source_text: str) -> str:
        if "納期" in source_text:
            return "対象範囲と希望納期の詳細をご教示いただけますでしょうか"
        if "確認" in source_text:
            return "確認対象の優先項目をご教示いただけますでしょうか"
        return "背景と期待されるアウトプットをご教示いただけますでしょうか"

    def _retone(self, text: str, selected_tone: DraftTone) -> tuple[str, str]:
        if selected_tone == DraftTone.BUSINESS_FORMAL:
            return f"承知いたしました。{text}", "retone: business_formal"
        if selected_tone == DraftTone.PROFESSIONAL_CONCISE:
            short = text.replace("ご連絡ありがとうございます。", "").replace("よろしくお願いします。", "")
            return short.strip(), "retone: professional_concise"
        if selected_tone == DraftTone.FRIENDLY_POLITE:
            if "ご連絡ありがとうございます。" in text:
                return text, "retone: friendly_polite"
            return f"ご連絡ありがとうございます。{text}", "retone: friendly_polite"
        if selected_tone == DraftTone.APOLOGY:
            if "申し訳ありません" in text:
                return text, "retone: apology"
            return f"返信が遅くなり申し訳ありません。{text}", "retone: apology"
        if selected_tone == DraftTone.DELAY_RESPONSE:
            return f"確認に少しお時間をいただけますと幸いです。{text}", "retone: delay_response"

        if "ご教示" in text:
            return text, "retone: clarification"
        return f"認識を合わせるため、詳細をご教示いただけますでしょうか。{text}", "retone: clarification"

    def _apply_instruction(self, text: str, instruction: str) -> tuple[str, list[str]]:
        working = text
        lowered = instruction.lower()
        actions: list[str] = []

        if "make it shorter" in lowered or "shorter" in lowered or "lebih singkat" in lowered:
            working = self._shorten_text(working)
            actions.append("shortened draft")

        remove_match = re.search(r"remove this context[:\-]?\s*(.+)$", instruction, re.IGNORECASE)
        if remove_match:
            phrase = remove_match.group(1).strip()
            if phrase:
                working = working.replace(phrase, "").replace("  ", " ").strip()
                actions.append(f"removed context: {phrase}")

        add_match = re.search(r"add this context[:\-]?\s*(.+)$", instruction, re.IGNORECASE)
        if add_match:
            phrase = add_match.group(1).strip()
            if phrase:
                if not working.endswith("。"):
                    working = f"{working}。"
                working = f"{working} 追記: {phrase}。"
                actions.append(f"added context: {phrase}")

        if "make it more polite" in lowered or "more polite" in lowered or "lebih sopan" in lowered:
            if "恐れ入りますが" not in working:
                working = f"恐れ入りますが、{working}"
            if "よろしくお願いいたします" not in working:
                if not working.endswith("。"):
                    working = f"{working}。"
                working = f"{working} よろしくお願いいたします。"
            actions.append("increased politeness")

        if not actions:
            actions.append("no rule matched; kept original draft")

        working = re.sub(r"\s+", " ", working).strip()
        return working, actions

    @staticmethod
    def _shorten_text(text: str) -> str:
        chunks = [chunk.strip() for chunk in re.split(r"。", text) if chunk.strip()]
        if not chunks:
            return text
        if len(chunks) == 1:
            return chunks[0] + "。"
        return "。".join(chunks[:2]) + "。"

    @staticmethod
    def _to_view(draft: Draft) -> DraftView:
        return DraftView(
            id=draft.id,
            target_conversation_id=draft.target_conversation_id,
            message_id=draft.message_id,
            status=draft.status,
            tone=draft.tone,
            urgency=draft.urgency,
            body_original=draft.body_original,
            body_translated=draft.body_translated,
            exact_message_body=draft.exact_message_body,
            updated_at=draft.updated_at,
        )
