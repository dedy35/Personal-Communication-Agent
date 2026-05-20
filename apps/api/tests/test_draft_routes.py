from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.routes.drafts import get_draft_service


class FakeDraftService:
    def generate_draft(self, payload):
        _ = payload
        return {
            "draft": {
                "id": 101,
                "target_conversation_id": 1,
                "message_id": 1,
                "status": "draft_ready",
                "tone": "business_formal",
                "urgency": "high",
                "body_original": "承知いたしました。確認のうえ、ご連絡いたします。",
                "body_translated": "Baik, saya akan cek dan mengabari.",
                "exact_message_body": "承知いたしました。確認のうえ、ご連絡いたします。",
                "applied_actions": [],
                "updated_at": datetime.now(tz=UTC).isoformat(),
            },
            "used_context": {
                "conversation_title": "Ticket",
                "contact_name": "Takahashi-san",
                "relationship_type": "senior",
                "platform_name": "line",
                "selected_tone": "business_formal",
                "urgency": "high",
                "practical_meaning": "Pengirim meminta konfirmasi.",
            },
        }

    def revise_draft(self, draft_id: int, payload):
        _ = payload
        return {
            "draft": {
                "id": draft_id,
                "target_conversation_id": 1,
                "message_id": 1,
                "status": "draft_ready",
                "tone": "business_formal",
                "urgency": "high",
                "body_original": "恐れ入りますが、承知いたしました。",
                "body_translated": "Mohon izin, baik saya pahami.",
                "exact_message_body": "恐れ入りますが、承知いたしました。",
                "applied_actions": ["increased politeness"],
                "updated_at": datetime.now(tz=UTC).isoformat(),
            }
        }


@pytest.mark.anyio
async def test_generate_and_revise_draft_routes() -> None:
    app = create_app()

    async def override_draft_service() -> FakeDraftService:
        return FakeDraftService()

    app.dependency_overrides[get_draft_service] = override_draft_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        generate_response = await client.post(
            "/drafts/generate",
            json={
                "conversation_id": 1,
                "source_message_id": 1,
                "selected_tone": "business_formal",
            },
        )
        revise_response = await client.post(
            "/drafts/101/revise",
            json={"instruction": "make it more polite"},
        )

    assert generate_response.status_code == 200
    assert revise_response.status_code == 200

    generate_data = generate_response.json()
    revise_data = revise_response.json()

    assert generate_data["draft"]["tone"] == "business_formal"
    assert "used_context" in generate_data
    assert revise_data["draft"]["id"] == 101
    assert revise_data["draft"]["applied_actions"][0] == "increased politeness"
