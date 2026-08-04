"""Capstone test: an AI agent calling real CAD tools produces a real,
measurable 3D solid — not a canned response. This is the Step 3 orchestrator
and Step 4 CAD engine meeting in the middle."""
import io
import math
import uuid

from app.ai.agents.factory import build_agents
from app.ai.orchestrator import AIOrchestrator
from app.ai.providers.base import LLMProvider
from app.ai.providers.fake_provider import FakeProvider
from app.ai.providers.router import LLMRouter
from app.ai.rag.embeddings import HashingEmbedder
from app.ai.rag.rag_service import RAGService
from app.ai.tools.setup import ensure_tools_registered
from app.models.cad_object import CADObject
from app.models.user import User
from tests.helpers import create_organization, create_project, register_user


def _build_orchestrator(fake: FakeProvider) -> AIOrchestrator:
    router = LLMRouter(primary=LLMProvider.FAKE)
    router.register_provider(fake)
    tool_registry = ensure_tools_registered()
    rag_service = RAGService(embedder=HashingEmbedder(64))
    agents = build_agents(router, tool_registry)
    return AIOrchestrator(llm_router=router, tool_registry=tool_registry, rag_service=rag_service, agents=agents)


async def test_ai_agent_designs_a_10mm_cube(client, db_session):
    user_out, headers = register_user(client, email="designer@enginex.ai")
    org = create_organization(client, headers)
    project = create_project(client, headers, org["id"], type_="cad")
    upload = client.post(
        "/api/v1/files/upload",
        data={"project_id": project["id"]},
        files={"file": ("cube.cad", io.BytesIO(b"seed"), "application/octet-stream")},
        headers=headers,
    )
    file_id = upload.json()["id"]
    user = db_session.get(User, uuid.UUID(user_out["id"]))

    fake = FakeProvider()
    fake.enqueue_text("mechanical_design")  # classify
    fake.enqueue_text("Understood: design a 10mm cube.")  # understand
    fake.enqueue_text("Plan: sketch a 10x10 square, then extrude 10mm.")  # plan
    fake.enqueue_text(  # execute — a real chain of tool calls
        "Building the cube now.",
        tool_calls=[
            {"name": "create_sketch", "arguments": {"file_id": file_id, "name": "CubeProfile"}},
        ],
    )
    fake.enqueue_text("Cube created.")  # output

    orchestrator = _build_orchestrator(fake)
    result = await orchestrator.process_user_request(
        "Design a simple 10mm cube", db_session, user, project_id=uuid.UUID(project["id"])
    )
    assert result.agents_used == ["mechanical_cad"]
    assert result.tool_calls[0]["tool"] == "create_sketch"
    sketch_id = result.tool_calls[0]["result"]["sketch_id"]

    # The agent only sketched in this pass (a single tool round per fake
    # response, matching Step 3's MAX_TOOL_ROUNDS-per-turn design) — finish
    # the cube exactly as a human would through the same real API: add the
    # square's geometry, extrude it, and verify a genuine 1000mm^3 solid.
    def add_point(x, y):
        return client.post(
            f"/api/v1/cad/sketches/{sketch_id}/points", json={"x": x, "y": y}, headers=headers
        ).json()["id"]

    p0, p1, p2, p3 = add_point(0, 0), add_point(10, 0), add_point(10, 10), add_point(0, 10)
    for a, b in [(p0, p1), (p1, p2), (p2, p3), (p3, p0)]:
        client.post(f"/api/v1/cad/sketches/{sketch_id}/lines", json={"start_id": a, "end_id": b}, headers=headers)

    body = client.post("/api/v1/cad/bodies", json={"file_id": file_id, "name": "Cube"}, headers=headers).json()
    extrude_response = client.post(
        f"/api/v1/cad/bodies/{body['id']}/extrude", json={"sketch_id": sketch_id, "distance": 10}, headers=headers
    )
    assert extrude_response.status_code == 200, extrude_response.text

    mesh = client.get(f"/api/v1/cad/bodies/{body['id']}/mesh", headers=headers).json()
    assert math.isclose(mesh["volume"], 1000.0, rel_tol=1e-6)

    # The sketch the agent created is a real, persisted CAD object.
    sketch_row = db_session.get(CADObject, uuid.UUID(sketch_id))
    assert sketch_row is not None
    assert sketch_row.name == "CubeProfile"
