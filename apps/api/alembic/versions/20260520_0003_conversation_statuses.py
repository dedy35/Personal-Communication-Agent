"""add conversation status field

Revision ID: 20260520_0003
Revises: 20260520_0002
Create Date: 2026-05-20 05:00:00.000000
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260520_0003"
down_revision: str | None = "20260520_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ALLOWED_STATUSES = (
    "need_reply",
    "draft_ready",
    "waiting_reply",
    "fyi_only",
    "sensitive",
    "archived",
)


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("status", sa.String(length=32), nullable=False, server_default="need_reply"),
    )

    op.create_check_constraint(
        "ck_conversations_status_allowed",
        "conversations",
        f"status IN {ALLOWED_STATUSES}",
    )

    op.execute(
        sa.text(
            """
            UPDATE conversations c
            SET status = CASE
                WHEN c.id IN (SELECT d.target_conversation_id FROM drafts d WHERE d.status = 'draft_ready') THEN 'draft_ready'
                WHEN c.sensitive_topic_detected = true THEN 'sensitive'
                WHEN c.requires_reply = true THEN 'need_reply'
                ELSE 'fyi_only'
            END
            """
        )
    )

    op.execute(sa.text("UPDATE conversations SET status='waiting_reply' WHERE id=3"))


def downgrade() -> None:
    op.drop_constraint("ck_conversations_status_allowed", "conversations", type_="check")
    op.drop_column("conversations", "status")
