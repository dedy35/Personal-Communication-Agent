from app.models import Base


def _column_names(table_name: str) -> set[str]:
    table = Base.metadata.tables[table_name]
    return {column.name for column in table.columns}


def test_required_tables_exist() -> None:
    expected_tables = {
        "platform_accounts",
        "contacts",
        "conversations",
        "messages",
        "conversation_summaries",
        "drafts",
        "approvals",
        "agent_chat_sessions",
        "agent_chat_messages",
        "audit_logs",
        "settings",
    }
    assert expected_tables.issubset(set(Base.metadata.tables.keys()))


def test_message_fields_for_language_and_nuance() -> None:
    columns = _column_names("messages")
    assert {"language", "body_original", "body_translated", "urgency", "requires_reply", "tone"}.issubset(columns)


def test_approval_safety_fields_exist() -> None:
    columns = _column_names("approvals")
    assert {"exact_message_body", "target_conversation_id", "group_extra_confirmed"}.issubset(columns)


def test_sensitive_topic_fields_exist() -> None:
    conversation_columns = _column_names("conversations")
    message_columns = _column_names("messages")
    draft_columns = _column_names("drafts")

    assert {"sensitive_topic_detected", "sensitive_topic_labels"}.issubset(conversation_columns)
    assert {"sensitive_topic_detected", "sensitive_topic_labels"}.issubset(message_columns)
    assert {"sensitive_topic_detected", "sensitive_topic_labels"}.issubset(draft_columns)


def test_conversation_status_field_exists() -> None:
    conversation_columns = _column_names("conversations")
    assert "status" in conversation_columns
