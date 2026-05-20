"""seed sample conversations for slack whatsapp and line

Revision ID: 20260520_0002
Revises: 20260520_0001
Create Date: 2026-05-20 00:10:00.000000
"""

from datetime import datetime, timezone
from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import column, table

# revision identifiers, used by Alembic.
revision: str = "20260520_0002"
down_revision: str | None = "20260520_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UTC_NOW = datetime(2026, 5, 20, 0, 10, 0, tzinfo=timezone.utc)


def upgrade() -> None:
    platform_accounts = table(
        "platform_accounts",
        column("id", sa.Integer),
        column("platform_name", sa.String),
        column("account_label", sa.String),
        column("external_account_id", sa.String),
        column("is_active", sa.Boolean),
        column("metadata_json", sa.JSON),
        column("created_at", sa.DateTime(timezone=True)),
        column("updated_at", sa.DateTime(timezone=True)),
    )
    contacts = table(
        "contacts",
        column("id", sa.Integer),
        column("platform_account_id", sa.Integer),
        column("external_contact_id", sa.String),
        column("display_name", sa.String),
        column("handle", sa.String),
        column("relationship_type", sa.String),
        column("preferred_language", sa.String),
        column("preferred_tone", sa.String),
        column("notes", sa.Text),
        column("sensitive_topic_detected", sa.Boolean),
        column("sensitive_topic_labels", sa.JSON),
        column("created_at", sa.DateTime(timezone=True)),
        column("updated_at", sa.DateTime(timezone=True)),
    )
    conversations = table(
        "conversations",
        column("id", sa.Integer),
        column("platform_account_id", sa.Integer),
        column("contact_id", sa.Integer),
        column("external_conversation_id", sa.String),
        column("conversation_type", sa.String),
        column("title", sa.String),
        column("language", sa.String),
        column("urgency", sa.String),
        column("requires_reply", sa.Boolean),
        column("sensitive_topic_detected", sa.Boolean),
        column("sensitive_topic_labels", sa.JSON),
        column("last_message_at", sa.DateTime(timezone=True)),
        column("created_at", sa.DateTime(timezone=True)),
        column("updated_at", sa.DateTime(timezone=True)),
    )
    messages = table(
        "messages",
        column("id", sa.Integer),
        column("conversation_id", sa.Integer),
        column("sender_contact_id", sa.Integer),
        column("direction", sa.String),
        column("language", sa.String),
        column("body_original", sa.Text),
        column("body_translated", sa.Text),
        column("urgency", sa.String),
        column("requires_reply", sa.Boolean),
        column("tone", sa.String),
        column("sensitive_topic_detected", sa.Boolean),
        column("sensitive_topic_labels", sa.JSON),
        column("source_message_ts", sa.DateTime(timezone=True)),
        column("created_at", sa.DateTime(timezone=True)),
        column("updated_at", sa.DateTime(timezone=True)),
    )
    conversation_summaries = table(
        "conversation_summaries",
        column("id", sa.Integer),
        column("conversation_id", sa.Integer),
        column("language", sa.String),
        column("summary_text", sa.Text),
        column("key_points", sa.JSON),
        column("urgency", sa.String),
        column("requires_reply", sa.Boolean),
        column("sensitive_topic_detected", sa.Boolean),
        column("sensitive_topic_labels", sa.JSON),
        column("created_at", sa.DateTime(timezone=True)),
        column("updated_at", sa.DateTime(timezone=True)),
    )
    drafts = table(
        "drafts",
        column("id", sa.Integer),
        column("message_id", sa.Integer),
        column("target_conversation_id", sa.Integer),
        column("language", sa.String),
        column("body_original", sa.Text),
        column("body_translated", sa.Text),
        column("exact_message_body", sa.Text),
        column("tone", sa.String),
        column("urgency", sa.String),
        column("requires_reply", sa.Boolean),
        column("status", sa.String),
        column("sensitive_topic_detected", sa.Boolean),
        column("sensitive_topic_labels", sa.JSON),
        column("created_at", sa.DateTime(timezone=True)),
        column("updated_at", sa.DateTime(timezone=True)),
    )
    approvals = table(
        "approvals",
        column("id", sa.Integer),
        column("draft_id", sa.Integer),
        column("approver_id", sa.String),
        column("target_conversation_id", sa.Integer),
        column("exact_message_body", sa.Text),
        column("group_extra_confirmed", sa.Boolean),
        column("decision", sa.String),
        column("sensitive_topic_detected", sa.Boolean),
        column("sensitive_topic_labels", sa.JSON),
        column("decision_reason", sa.Text),
        column("created_at", sa.DateTime(timezone=True)),
        column("updated_at", sa.DateTime(timezone=True)),
    )
    settings = table(
        "settings",
        column("id", sa.Integer),
        column("key", sa.String),
        column("value_text", sa.Text),
        column("value_json", sa.JSON),
        column("is_secret", sa.Boolean),
        column("created_at", sa.DateTime(timezone=True)),
        column("updated_at", sa.DateTime(timezone=True)),
    )

    op.bulk_insert(
        platform_accounts,
        [
            {
                "id": 1,
                "platform_name": "slack",
                "account_label": "Work Slack",
                "external_account_id": "T_WORK_001",
                "is_active": True,
                "metadata_json": None,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            },
            {
                "id": 2,
                "platform_name": "whatsapp",
                "account_label": "WhatsApp Personal",
                "external_account_id": "wa-main",
                "is_active": True,
                "metadata_json": None,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            },
            {
                "id": 3,
                "platform_name": "line",
                "account_label": "LINE Japan",
                "external_account_id": "line-main",
                "is_active": True,
                "metadata_json": None,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            },
        ],
    )

    op.bulk_insert(
        contacts,
        [
            {
                "id": 1,
                "platform_account_id": 1,
                "external_contact_id": "U_SLACK_TAKAHASHI",
                "display_name": "Takahashi-san",
                "handle": "@takahashi",
                "relationship_type": "senior",
                "preferred_language": "ja",
                "preferred_tone": "business_formal",
                "notes": "Engineering reviewer",
                "sensitive_topic_detected": False,
                "sensitive_topic_labels": None,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            },
            {
                "id": 2,
                "platform_account_id": 2,
                "external_contact_id": "WA_HAYATO",
                "display_name": "Hayato",
                "handle": None,
                "relationship_type": "colleague",
                "preferred_language": "ja",
                "preferred_tone": "polite_short",
                "notes": "Freelance discussion",
                "sensitive_topic_detected": True,
                "sensitive_topic_labels": None,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            },
            {
                "id": 3,
                "platform_account_id": 3,
                "external_contact_id": "LINE_SATO",
                "display_name": "Sato-san",
                "handle": None,
                "relationship_type": "client",
                "preferred_language": "ja",
                "preferred_tone": "formal",
                "notes": "Client-side coordinator",
                "sensitive_topic_detected": False,
                "sensitive_topic_labels": None,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            },
        ],
    )

    op.bulk_insert(
        conversations,
        [
            {
                "id": 1,
                "platform_account_id": 1,
                "contact_id": 1,
                "external_conversation_id": "C-SLACK-TICKET-1580",
                "conversation_type": "dm",
                "title": "Ticket 1580 Follow-up",
                "language": "ja",
                "urgency": "high",
                "requires_reply": True,
                "sensitive_topic_detected": False,
                "sensitive_topic_labels": None,
                "last_message_at": UTC_NOW,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            },
            {
                "id": 2,
                "platform_account_id": 2,
                "contact_id": 2,
                "external_conversation_id": "WA-CHAT-HAYATO",
                "conversation_type": "dm",
                "title": "Freelance Offer Discussion",
                "language": "ja",
                "urgency": "medium",
                "requires_reply": True,
                "sensitive_topic_detected": True,
                "sensitive_topic_labels": None,
                "last_message_at": UTC_NOW,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            },
            {
                "id": 3,
                "platform_account_id": 3,
                "contact_id": 3,
                "external_conversation_id": "LINE-SATO-DELIVERY",
                "conversation_type": "dm",
                "title": "Delivery Date Confirmation",
                "language": "ja",
                "urgency": "high",
                "requires_reply": True,
                "sensitive_topic_detected": False,
                "sensitive_topic_labels": None,
                "last_message_at": UTC_NOW,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            },
        ],
    )

    op.bulk_insert(
        messages,
        [
            {
                "id": 1,
                "conversation_id": 1,
                "sender_contact_id": 1,
                "direction": "incoming",
                "language": "ja",
                "body_original": "本日中に確認してご報告いただけますか。",
                "body_translated": "Bisakah Anda cek dan melaporkan hari ini?",
                "urgency": "high",
                "requires_reply": True,
                "tone": "formal_request",
                "sensitive_topic_detected": False,
                "sensitive_topic_labels": None,
                "source_message_ts": UTC_NOW,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            },
            {
                "id": 2,
                "conversation_id": 2,
                "sender_contact_id": 2,
                "direction": "incoming",
                "language": "ja",
                "body_original": "今の会社に内緒で週15時間なら手伝える？",
                "body_translated": "Bisakah bantu 15 jam per minggu tanpa diketahui perusahaan sekarang?",
                "urgency": "medium",
                "requires_reply": True,
                "tone": "casual_sensitive",
                "sensitive_topic_detected": True,
                "sensitive_topic_labels": None,
                "source_message_ts": UTC_NOW,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            },
            {
                "id": 3,
                "conversation_id": 3,
                "sender_contact_id": 3,
                "direction": "incoming",
                "language": "ja",
                "body_original": "納期は明日までに確定できますでしょうか。",
                "body_translated": "Apakah tenggat bisa dipastikan paling lambat besok?",
                "urgency": "high",
                "requires_reply": True,
                "tone": "polite_business",
                "sensitive_topic_detected": False,
                "sensitive_topic_labels": None,
                "source_message_ts": UTC_NOW,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            },
        ],
    )

    op.bulk_insert(
        conversation_summaries,
        [
            {
                "id": 1,
                "conversation_id": 1,
                "language": "id",
                "summary_text": "Takahashi-san meminta update verifikasi ticket 1580 hari ini.",
                "key_points": None,
                "urgency": "high",
                "requires_reply": True,
                "sensitive_topic_detected": False,
                "sensitive_topic_labels": None,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            },
            {
                "id": 2,
                "conversation_id": 2,
                "language": "id",
                "summary_text": "Diskusi freelance berpotensi konflik dengan pekerjaan utama.",
                "key_points": None,
                "urgency": "medium",
                "requires_reply": True,
                "sensitive_topic_detected": True,
                "sensitive_topic_labels": None,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            },
            {
                "id": 3,
                "conversation_id": 3,
                "language": "id",
                "summary_text": "Sato-san meminta konfirmasi tenggat final sebelum besok.",
                "key_points": None,
                "urgency": "high",
                "requires_reply": True,
                "sensitive_topic_detected": False,
                "sensitive_topic_labels": None,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            },
        ],
    )

    op.bulk_insert(
        drafts,
        [
            {
                "id": 1,
                "message_id": 1,
                "target_conversation_id": 1,
                "language": "ja",
                "body_original": "承知いたしました。本日中に確認し、ご報告いたします。",
                "body_translated": "Baik, saya akan cek dan melaporkan hari ini.",
                "exact_message_body": "承知いたしました。本日中に確認し、ご報告いたします。",
                "tone": "business_formal",
                "urgency": "high",
                "requires_reply": True,
                "status": "draft_ready",
                "sensitive_topic_detected": False,
                "sensitive_topic_labels": None,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            }
        ],
    )

    op.bulk_insert(
        approvals,
        [
            {
                "id": 1,
                "draft_id": 1,
                "approver_id": "owner",
                "target_conversation_id": 1,
                "exact_message_body": "承知いたしました。本日中に確認し、ご報告いたします。",
                "group_extra_confirmed": True,
                "decision": "approved",
                "sensitive_topic_detected": False,
                "sensitive_topic_labels": None,
                "decision_reason": "Sample seeded approval",
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            }
        ],
    )

    op.bulk_insert(
        settings,
        [
            {
                "id": 1,
                "key": "communication.default_language",
                "value_text": "id",
                "value_json": None,
                "is_secret": False,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            },
            {
                "id": 2,
                "key": "approval.strict_mode",
                "value_text": "true",
                "value_json": None,
                "is_secret": False,
                "created_at": UTC_NOW,
                "updated_at": UTC_NOW,
            },
        ],
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM approvals WHERE id IN (1)"))
    op.execute(sa.text("DELETE FROM drafts WHERE id IN (1)"))
    op.execute(sa.text("DELETE FROM conversation_summaries WHERE id IN (1, 2, 3)"))
    op.execute(sa.text("DELETE FROM messages WHERE id IN (1, 2, 3)"))
    op.execute(sa.text("DELETE FROM conversations WHERE id IN (1, 2, 3)"))
    op.execute(sa.text("DELETE FROM contacts WHERE id IN (1, 2, 3)"))
    op.execute(sa.text("DELETE FROM platform_accounts WHERE id IN (1, 2, 3)"))
    op.execute(sa.text("DELETE FROM settings WHERE id IN (1, 2)"))
