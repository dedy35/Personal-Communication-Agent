import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.routes.dashboard_data import get_dashboard_service
from app.schemas.dashboard import STATUS_VALUES


class FakeDashboardService:
    def list_platform_statuses(self):
        return [
            {
                "platform_account_id": 1,
                "platform_name": "slack",
                "account_label": "Work Slack",
                "is_active": True,
                "statuses": {status: (1 if status == "need_reply" else 0) for status in STATUS_VALUES},
                "total_conversations": 1,
            }
        ]

    def list_conversations(self, platform, status, limit, offset):
        _ = (platform, status, limit, offset)
        return (
            [
                {
                    "id": 1,
                    "platform_name": "slack",
                    "title": "Ticket 1580",
                    "status": "need_reply",
                    "urgency": "high",
                    "requires_reply": True,
                    "sensitive_topic_detected": False,
                    "contact_name": "Takahashi-san",
                    "language": "ja",
                    "last_message_at": None,
                    "last_message_preview": "確認お願いします",
                }
            ],
            1,
        )

    def list_messages(self, conversation_id, limit):
        _ = (conversation_id, limit)
        return [
            {
                "id": 1,
                "conversation_id": 1,
                "direction": "incoming",
                "language": "ja",
                "body_original": "確認お願いします",
                "body_translated": "Mohon dicek",
                "urgency": "high",
                "requires_reply": True,
                "tone": "polite",
                "sensitive_topic_detected": False,
                "source_message_ts": None,
            }
        ]

    def list_drafts(self, status, limit, offset):
        _ = (status, limit, offset)
        return (
            [
                {
                    "id": 1,
                    "target_conversation_id": 1,
                    "message_id": 1,
                    "status": "draft_ready",
                    "language": "ja",
                    "body_original": "承知しました",
                    "body_translated": "Baik",
                    "exact_message_body": "承知しました",
                    "tone": "formal",
                    "urgency": "high",
                    "requires_reply": True,
                    "sensitive_topic_detected": False,
                }
            ],
            1,
        )

    def get_dashboard_counts(self):
        return {
            "statuses": {status: 0 for status in STATUS_VALUES},
            "total_conversations": 1,
            "total_messages": 1,
            "total_drafts": 1,
            "draft_ready_count": 1,
            "sensitive_count": 0,
        }


@pytest.mark.anyio
async def test_dashboard_endpoints() -> None:
    app = create_app()
    async def override_dashboard_service() -> FakeDashboardService:
        return FakeDashboardService()

    app.dependency_overrides[get_dashboard_service] = override_dashboard_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        platforms = await client.get("/platforms/statuses")
        conversations = await client.get("/conversations")
        messages = await client.get("/conversations/1/messages")
        drafts = await client.get("/drafts")
        counts = await client.get("/dashboard/counts")

    assert platforms.status_code == 200
    assert conversations.status_code == 200
    assert messages.status_code == 200
    assert drafts.status_code == 200
    assert counts.status_code == 200

    assert platforms.json()["items"][0]["platform_name"] == "slack"
    assert conversations.json()["items"][0]["status"] == "need_reply"
    assert messages.json()["items"][0]["body_original"] == "確認お願いします"
    assert drafts.json()["items"][0]["status"] == "draft_ready"
    assert "statuses" in counts.json()
