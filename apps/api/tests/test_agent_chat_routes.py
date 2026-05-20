import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.routes.agent_chat import get_agent_service


class FakeAgentService:
    def chat(self, message: str, session_key: str | None, language: str | None = None):
        _ = (message, session_key, language)
        return {
            "session_key": "chat-test-001",
            "matched_intent": "daily_summary",
            "reply": "Daily narrative summary:\n- Need reply: 1",
            "messages": [
                {
                    "role": "user",
                    "body": "daily narrative summary",
                    "language": "en",
                    "created_at": "2026-05-20T00:00:00+00:00",
                },
                {
                    "role": "assistant",
                    "body": "Daily narrative summary:\n- Need reply: 1",
                    "language": "en",
                    "created_at": "2026-05-20T00:00:01+00:00",
                },
            ],
        }


@pytest.mark.anyio
async def test_agent_chat_endpoint() -> None:
    app = create_app()

    async def override_agent_service() -> FakeAgentService:
        return FakeAgentService()

    app.dependency_overrides[get_agent_service] = override_agent_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/agent/chat",
            json={
                "message": "daily narrative summary",
                "session_key": "chat-test-001",
                "language": "en",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["session_key"] == "chat-test-001"
    assert data["matched_intent"] == "daily_summary"
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][1]["role"] == "assistant"
