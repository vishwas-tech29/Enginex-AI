# API

## Base URL

- Local: `http://localhost:8000`
- All REST routes are versioned under `/api/v1`. WebSocket routes are not
  (`/ws/files/{file_id}`).
- Interactive docs (Swagger UI) are served by FastAPI at `/docs`; the raw
  schema is at `/openapi.json`. `docs/architecture/api-spec.yaml` is an
  export of that same schema (see
  `services/backend/app/scripts/export_openapi.py`) — regenerate it with
  `python -m app.scripts.export_openapi` after changing routes, rather than
  hand-editing it.

## Authentication

Bearer JWT for HTTP routes. Obtain a token pair from `/api/v1/auth/register`
or `/api/v1/auth/login`, then send:

```
Authorization: Bearer <access_token>
```

Access tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30 min);
use `/api/v1/auth/refresh` with the refresh token to get a new pair.

WebSocket connections can't set custom headers from a browser, so both
`/ws/files/{file_id}` and `/ws/ai/chats/{chat_id}` take the access token as
a query parameter instead: `wss://.../ws/files/{file_id}?token=<access_token>`.

## Endpoint groups

See `docs/architecture/api-spec.yaml` (or `/docs`) for the full request/response
schemas. By domain:

| Domain | Status | Notes |
| --- | --- | --- |
| Authentication | Real | register/login/refresh/logout/me |
| Users | Real | profile get/update |
| Organizations, Teams | Real | owner-based access; team membership stored inline |
| Projects | Real | RBAC (owner/editor/viewer), share/invite/members |
| Folders | Real | CRUD + move |
| Files | Real | upload/download/versions/revert, local-disk or S3 storage |
| Components, Symbols, Footprints | Real | search/list; symbols & footprints also creatable |
| Simulation | Real API, no engine | job lifecycle (queued/cancelled) persists; nothing executes jobs yet |
| CAD | Real engine | sketch CRUD + real constraint solver; extrude/revolve/fillet/chamfer/boolean run on a CadQuery/OpenCascade kernel; STEP/STL/OBJ export from real geometry; assemblies with motion constraints and collision detection — see `services/backend/app/cad/` |
| PCB | Real persistence, stub engine | board/component CRUD is real; DRC/ERC/Gerber/BOM export return `501` |
| AI | Real | multi-provider router (OpenAI/Anthropic/Gemini/Groq/Together/OpenRouter/Azure/Ollama) with automatic fallback, 10 LangGraph agents, 27 tools wired to real CAD/PCB/component/simulation services, RAG (Qdrant), usage tracking. Runs on a no-key fake provider when no real provider is configured — see below |
| WebSocket collaboration | Real | Yjs (`y-py`) CRDT sync + presence, see below |
| WebSocket AI streaming | Real | `/ws/ai/chats/{chat_id}` streams agent lifecycle events, see below |

## Real-time collaboration

`/ws/files/{file_id}` is a per-file collaborative room. Wire format is a
custom JSON envelope (not the npm `y-websocket` binary protocol) — see
`services/backend/app/websockets/manager.py` for the exact message shapes
and the rationale. The payload inside `update` messages is a genuine Yjs
update (produced/applied via `y-py`), so multiple clients editing
concurrently merge via real CRDT semantics, not last-write-wins. Document
state persists to the `ydoc_snapshots` table when the last client in a room
disconnects, and rehydrates on the next connection.

## AI system

`POST /api/v1/ai/chats/{chat_id}/messages` and `/ws/ai/chats/{chat_id}` both
run the same pipeline (`app/ai/orchestrator.py`):

1. Classify the request into 1-2 categories (`app/ai/orchestrator.py:INTENT_TO_AGENT`)
2. Best-effort RAG context retrieval (never fails the request)
3. Dispatch to the matching specialist agent(s) — each a small LangGraph
   graph (understand → plan → execute tools → output)
4. If more than one agent ran, synthesize their results into one response
5. Log token usage/cost to `usage_logs` and enforce `AI_MAX_DAILY_COST_USD`

No LLM provider is required to run this — with no API keys configured, the
router falls back to a deterministic fake provider, so the full pipeline
(routing, tool execution, persistence, streaming) still works end to end;
set any of `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` / etc.
(see `.env.example`) to use a real model.

The WebSocket variant streams intermediate events as they happen:
`ack`, `thinking`, `intent_classified`, `agent_started`, `tool_called`,
`tool_result`, `agent_completed`, then a final `response` and `done`.

## Error format

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Project with ID <uuid> not found",
    "status_code": 404
  }
}
```

`code` is present for errors raised via the `app.core.exceptions` hierarchy
(`NotFoundError`, `ForbiddenError`, `ConflictError`, `ValidationError`,
`EngineNotImplementedError`); plain `HTTPException`s omit it. Validation
errors (422) additionally include a `details` array with per-field messages,
matching FastAPI's default `RequestValidationError` shape.
