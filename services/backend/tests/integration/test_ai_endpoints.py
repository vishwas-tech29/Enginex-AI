from app.ai.agents.factory import build_agents
from app.ai.orchestrator import AIOrchestrator
from app.ai.providers.base import LLMProvider
from app.ai.providers.fake_provider import FakeProvider
from app.ai.providers.router import LLMRouter
from app.ai.rag.embeddings import HashingEmbedder
from app.ai.rag.rag_service import RAGService
from app.ai.setup import get_orchestrator
from app.ai.tools.setup import ensure_tools_registered
from app.main import app
from tests.helpers import register_user


def _fake_orchestrator(fake: FakeProvider) -> AIOrchestrator:
    router = LLMRouter(primary=LLMProvider.FAKE)
    router.register_provider(fake)
    tool_registry = ensure_tools_registered()
    rag_service = RAGService(embedder=HashingEmbedder(64))
    agents = build_agents(router, tool_registry)
    return AIOrchestrator(llm_router=router, tool_registry=tool_registry, rag_service=rag_service, agents=agents)


def _override_orchestrator(fake: FakeProvider):
    orchestrator = _fake_orchestrator(fake)
    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    return orchestrator


def test_post_message_uses_real_orchestrator_pipeline(client):
    _, headers = register_user(client, email="aiendpoint1@enginex.ai")
    chat = client.post("/api/v1/ai/chats", json={"title": "Firmware help"}, headers=headers).json()

    fake = FakeProvider()
    fake.enqueue_text("firmware")
    fake.enqueue_text("Understood: blink an LED.")
    fake.enqueue_text("Plan: toggle GPIO in a loop.")
    fake.enqueue_text("Here's your blink firmware plan.")
    _override_orchestrator(fake)

    try:
        response = client.post(
            f"/api/v1/ai/chats/{chat['id']}/messages",
            json={"content": "Write blink firmware for STM32"},
            headers=headers,
        )
        assert response.status_code == 201, response.text
        messages = response.json()
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Here's your blink firmware plan."
    finally:
        app.dependency_overrides.pop(get_orchestrator, None)


def test_websocket_ai_streaming_emits_lifecycle_events(client):
    _, headers = register_user(client, email="aiendpoint2@enginex.ai")
    chat = client.post("/api/v1/ai/chats", json={"title": "Docs help"}, headers=headers).json()
    token = headers["Authorization"].split(" ")[1]

    fake = FakeProvider()
    fake.enqueue_text("documentation")
    fake.enqueue_text("Understood: summarize the project.")
    fake.enqueue_text("Plan: call get_project_summary if a project is given.")
    fake.enqueue_text("No tool call needed here.")
    fake.enqueue_text("Here is a documentation outline.")
    _override_orchestrator(fake)

    try:
        with client.websocket_connect(f"/ws/ai/chats/{chat['id']}?token={token}") as ws:
            ws.send_json({"id": "1", "message": "Draft a documentation outline"})

            event_types = []
            for _ in range(20):
                event = ws.receive_json()
                event_types.append(event["type"])
                if event["type"] == "done":
                    break

            assert event_types[0] == "ack"
            assert "response" in event_types
            assert event_types[-1] == "done"
            assert "intent_classified" in event_types
            assert "agent_started" in event_types
            assert "agent_completed" in event_types
    finally:
        app.dependency_overrides.pop(get_orchestrator, None)


def test_websocket_ai_rejects_other_users_chat(client):
    owner_out, owner_headers = register_user(client, email="aiendpoint3owner@enginex.ai")
    chat = client.post("/api/v1/ai/chats", json={"title": "Private"}, headers=owner_headers).json()

    _, intruder_headers = register_user(client, email="aiendpoint3intruder@enginex.ai")
    intruder_token = intruder_headers["Authorization"].split(" ")[1]

    try:
        with client.websocket_connect(f"/ws/ai/chats/{chat['id']}?token={intruder_token}") as ws:
            ws.receive_json()
        assert False, "expected the connection to be closed"
    except Exception:
        pass


def test_list_providers_reflects_configured_keys(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "anthropic_api_key", "sk-test-key")
    monkeypatch.setattr(settings, "openai_api_key", None)

    _, headers = register_user(client, email="aiendpoint4@enginex.ai")
    response = client.get("/api/v1/ai/providers", headers=headers)
    assert response.status_code == 200
    providers = {p["name"]: p["configured"] for p in response.json()}
    assert providers["anthropic"] is True
    assert providers["openai"] is False
    assert providers["ollama"] is True
