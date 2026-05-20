"""initial schema for personal communication agent

Revision ID: 20260520_0001
Revises: None
Create Date: 2026-05-20 00:00:01.000000
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260520_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "platform_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("platform_name", sa.String(length=32), nullable=False),
        sa.Column("account_label", sa.String(length=120), nullable=False),
        sa.Column("external_account_id", sa.String(length=191), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("platform_name", "account_label", name="uq_platform_accounts_platform_name_account_label"),
    )
    op.create_index("ix_platform_accounts_platform_name", "platform_accounts", ["platform_name"])

    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("platform_account_id", sa.Integer(), nullable=False),
        sa.Column("external_contact_id", sa.String(length=191), nullable=True),
        sa.Column("display_name", sa.String(length=191), nullable=False),
        sa.Column("handle", sa.String(length=191), nullable=True),
        sa.Column("relationship_type", sa.String(length=64), nullable=True),
        sa.Column("preferred_language", sa.String(length=16), nullable=True),
        sa.Column("preferred_tone", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sensitive_topic_detected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sensitive_topic_labels", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["platform_account_id"], ["platform_accounts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("platform_account_id", "external_contact_id", name="uq_contacts_platform_account_id_external_contact_id"),
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("platform_account_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("external_conversation_id", sa.String(length=191), nullable=True),
        sa.Column("conversation_type", sa.String(length=32), nullable=False, server_default="dm"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("urgency", sa.String(length=16), nullable=True),
        sa.Column("requires_reply", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sensitive_topic_detected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sensitive_topic_labels", sa.JSON(), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["platform_account_id"], ["platform_accounts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("platform_account_id", "external_conversation_id", name="uq_conversations_platform_account_id_external_conversation_id"),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("sender_contact_id", sa.Integer(), nullable=True),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("body_original", sa.Text(), nullable=False),
        sa.Column("body_translated", sa.Text(), nullable=True),
        sa.Column("urgency", sa.String(length=16), nullable=True),
        sa.Column("requires_reply", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("tone", sa.String(length=64), nullable=True),
        sa.Column("sensitive_topic_detected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sensitive_topic_labels", sa.JSON(), nullable=True),
        sa.Column("source_message_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_contact_id"], ["contacts.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    op.create_table(
        "conversation_summaries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("key_points", sa.JSON(), nullable=True),
        sa.Column("urgency", sa.String(length=16), nullable=True),
        sa.Column("requires_reply", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sensitive_topic_detected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sensitive_topic_labels", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_conversation_summaries_conversation_id", "conversation_summaries", ["conversation_id"])

    op.create_table(
        "drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("target_conversation_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("body_original", sa.Text(), nullable=False),
        sa.Column("body_translated", sa.Text(), nullable=True),
        sa.Column("exact_message_body", sa.Text(), nullable=False),
        sa.Column("tone", sa.String(length=64), nullable=True),
        sa.Column("urgency", sa.String(length=16), nullable=True),
        sa.Column("requires_reply", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft_ready"),
        sa.Column("sensitive_topic_detected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sensitive_topic_labels", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_conversation_id"], ["conversations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_drafts_target_conversation_id", "drafts", ["target_conversation_id"])

    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("draft_id", sa.Integer(), nullable=False),
        sa.Column("approver_id", sa.String(length=128), nullable=True),
        sa.Column("target_conversation_id", sa.Integer(), nullable=False),
        sa.Column("exact_message_body", sa.Text(), nullable=False),
        sa.Column("group_extra_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("decision", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("sensitive_topic_detected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sensitive_topic_labels", sa.JSON(), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["draft_id"], ["drafts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_conversation_id"], ["conversations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_approvals_draft_id", "approvals", ["draft_id"])

    op.create_table(
        "agent_chat_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_key", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=191), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("session_key", name="uq_agent_chat_sessions_session_key"),
    )
    op.create_index("ix_agent_chat_sessions_session_key", "agent_chat_sessions", ["session_key"])

    op.create_table(
        "agent_chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["session_id"], ["agent_chat_sessions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_agent_chat_messages_session_id", "agent_chat_messages", ["session_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=True),
        sa.Column("details_json", sa.JSON(), nullable=True),
        sa.Column("exact_message_body", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])

    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_json", sa.JSON(), nullable=True),
        sa.Column("is_secret", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("key", name="uq_settings_key"),
    )
    op.create_index("ix_settings_key", "settings", ["key"])


def downgrade() -> None:
    op.drop_index("ix_settings_key", table_name="settings")
    op.drop_table("settings")

    op.drop_index("ix_audit_logs_event_type", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_agent_chat_messages_session_id", table_name="agent_chat_messages")
    op.drop_table("agent_chat_messages")

    op.drop_index("ix_agent_chat_sessions_session_key", table_name="agent_chat_sessions")
    op.drop_table("agent_chat_sessions")

    op.drop_index("ix_approvals_draft_id", table_name="approvals")
    op.drop_table("approvals")

    op.drop_index("ix_drafts_target_conversation_id", table_name="drafts")
    op.drop_table("drafts")

    op.drop_index("ix_conversation_summaries_conversation_id", table_name="conversation_summaries")
    op.drop_table("conversation_summaries")

    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")

    op.drop_table("conversations")
    op.drop_table("contacts")

    op.drop_index("ix_platform_accounts_platform_name", table_name="platform_accounts")
    op.drop_table("platform_accounts")
