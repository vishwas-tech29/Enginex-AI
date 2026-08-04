import io
import uuid
from datetime import datetime, timezone

import pytest

from app.ai.agents.factory import build_agents
from app.ai.orchestrator import AIOrchestrator, DailyCostLimitExceededError
from app.ai.providers.base import LLMMessage, LLMProvider, LLMProviderError, LLMResponse, BaseLLMProvider
from app.ai.providers.fake_provider import FakeProvider
from app.ai.providers.router import LLMRouter
from app.ai.rag.embeddings import HashingEmbedder
from app.ai.rag.rag_service import RAGService
from app.ai.tools.setup import ensure_tools_registered
from app.models.cad_object import CADObject
from app.models.usage_log import UsageLog
from app.models.user import User
from tests.helpers import create_organization, create_project, register_user


def _build_orchestrator(fake: FakeProvider) -> AIOrchestrator:
    router = LLMRouter(primary=LLMProvider.FAKE)
    router.register_provider(fake)
    tool_registry = ensure_tools_registered()
    rag_service = RAGService(embedder=HashingEmbedder(64))
    agents = build_agents(router, tool_registry)
    return AIOrchestrator(llm_router=router, tool_registry=tool_registry, rag_service=rag_service, agents=agents)


def _upload_file(client, headers, project_id):
    response = client.post(
        "/api/v1/files/upload",
        data={"project_id": project_id},
        files={"file": ("part.cad", io.BytesIO(b"seed"), "application/octet-stream")},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_single_intent_routes_to_matching_agent(client, db_session):
    user_out, headers = register_user(client, email="orch1@enginex.ai")
    user = db_session.get(User, uuid.UUID(user_out["id"]))

    fake = FakeProvider()
    fake.enqueue_text("firmware")  # classify_intents
    fake.enqueue_text("Understood: blink an LED via GPIO toggle.")  # understand
    fake.enqueue_text("Plan: configure GPIO, write toggle loop.")  # plan
    fake.enqueue_text("Here is blink firmware guidance.")  # output (firmware has no tools -> no execute step)
    orchestrator = _build_orchestrator(fake)

    result = await orchestrator.process_user_request("Write blink firmware for an STM32", db_session, user)

    assert result.agents_used == ["firmware"]
    assert result.response == "Here is blink firmware guidance."
    assert result.tokens_used["input"] > 0
    assert result.intents == ["firmware"]


@pytest.mark.asyncio
async def test_multi_intent_dispatches_both_agents_and_synthesizes(client, db_session):
    user_out, headers = register_user(client, email="orch2@enginex.ai")
    user = db_session.get(User, uuid.UUID(user_out["id"]))

    fake = FakeProvider()
    fake.enqueue_text("electronics, pcb_design")  # classify
    # electronics agent: understand, plan, execute (has tools), output
    fake.enqueue_text("Electronics: need a current-limiting resistor.")
    fake.enqueue_text("Electronics plan: search components.")
    fake.enqueue_text("Electronics: no tool call needed.")
    fake.enqueue_text("Electronics result: use a 220ohm resistor with a red LED at 5V.")
    # pcb_design agent: understand, plan, execute (has tools), output
    fake.enqueue_text("PCB: place the resistor and LED footprints.")
    fake.enqueue_text("PCB plan: place components on board.")
    fake.enqueue_text("PCB: no tool call needed.")
    fake.enqueue_text("PCB result: footprints placed on a single-layer board.")
    # synthesis
    fake.enqueue_text("Combined: use a 220ohm resistor with the red LED; footprints placed on the board.")

    orchestrator = _build_orchestrator(fake)
    result = await orchestrator.process_user_request(
        "Design a simple LED circuit with current limiting resistor on 5V", db_session, user
    )

    assert set(result.agents_used) == {"electronics", "pcb_design"}
    assert "resistor" in result.response.lower() or "ohm" in result.response.lower()


@pytest.mark.asyncio
async def test_agent_tool_call_persists_real_data(client, db_session):
    user_out, headers = register_user(client, email="orch3@enginex.ai")
    org = create_organization(client, headers)
    project = create_project(client, headers, org["id"], type_="cad")
    file_obj = _upload_file(client, headers, project["id"])
    user = db_session.get(User, uuid.UUID(user_out["id"]))

    fake = FakeProvider()
    fake.enqueue_text("mechanical_design")  # classify
    fake.enqueue_text("Understood: create a base sketch.")  # understand
    fake.enqueue_text("Plan: call create_sketch.")  # plan
    fake.enqueue_text(  # execute — real tool call
        "Creating the sketch now.",
        tool_calls=[{"name": "create_sketch", "arguments": {"file_id": file_obj["id"], "name": "BaseSketch"}}],
    )
    fake.enqueue_text("Created a sketch named BaseSketch.")  # output

    orchestrator = _build_orchestrator(fake)
    result = await orchestrator.process_user_request(
        "Create a base sketch for this part", db_session, user, project_id=uuid.UUID(project["id"])
    )

    assert result.agents_used == ["mechanical_cad"]
    assert result.tool_calls[0]["tool"] == "create_sketch"
    assert result.tool_calls[0]["success"] is True

    created = db_session.query(CADObject).filter(CADObject.name == "BaseSketch").first()
    assert created is not None
    assert str(created.file_id) == file_obj["id"]


@pytest.mark.asyncio
async def test_provider_failover_falls_back_to_next_provider():
    class BrokenProvider(BaseLLMProvider):
        provider_type = LLMProvider.OPENAI

        async def call_model(self, model, messages, tools=None, temperature=0.7, max_tokens=4096):
            raise LLMProviderError("simulated outage")

        def calculate_cost(self, model, tokens_input, tokens_output):
            return 0.0

    router = LLMRouter(primary=LLMProvider.OPENAI, fallback_chain=[LLMProvider.FAKE])
    router.register_provider(BrokenProvider())
    router.register_provider(FakeProvider())

    response = await router.call_model("gpt-4o", [LLMMessage(role="user", content="hi")])
    assert response.provider == "fake"
    assert response.content


@pytest.mark.asyncio
async def test_all_providers_failing_raises():
    class BrokenProvider(BaseLLMProvider):
        provider_type = LLMProvider.OPENAI

        async def call_model(self, model, messages, tools=None, temperature=0.7, max_tokens=4096):
            raise LLMProviderError("simulated outage")

        def calculate_cost(self, model, tokens_input, tokens_output):
            return 0.0

    from app.ai.providers.router import AllProvidersFailedError

    router = LLMRouter(primary=LLMProvider.OPENAI, fallback_chain=[])
    router.register_provider(BrokenProvider())

    with pytest.raises(AllProvidersFailedError):
        await router.call_model("gpt-4o", [LLMMessage(role="user", content="hi")])


@pytest.mark.asyncio
async def test_daily_cost_limit_blocks_further_requests(client, db_session, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ai_max_daily_cost_usd", 0.01)

    user_out, headers = register_user(client, email="orch4@enginex.ai")
    org = create_organization(client, headers)
    user = db_session.get(User, uuid.UUID(user_out["id"]))

    from app.models.organization import Organization

    organization = db_session.get(Organization, uuid.UUID(org["id"]))
    db_session.add(
        UsageLog(
            organization_id=organization.id,
            user_id=user.id,
            operation="agent:test",
            tokens_used=1000,
            cost_usd=1.0,
            created_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    fake = FakeProvider()
    orchestrator = _build_orchestrator(fake)

    with pytest.raises(DailyCostLimitExceededError):
        await orchestrator.process_user_request("Design something", db_session, user)


@pytest.mark.asyncio
async def test_rag_search_returns_ranked_results():
    from app.scripts.seed_knowledge import COLLECTIONS

    rag = RAGService(embedder=HashingEmbedder(128))
    for collection, docs in COLLECTIONS.items():
        if docs:
            await rag.index_documents(collection, docs)

    results = await rag.search("decoupling capacitor placement best practices", "app_notes", limit=3)
    assert len(results) > 0
    assert results[0]["score"] >= results[-1]["score"]

    all_results = await rag.search_all_collections("PCB design rules")
    assert set(all_results.keys()) == {
        "datasheets", "standards", "reference_designs", "app_notes", "company_knowledge"
    }
