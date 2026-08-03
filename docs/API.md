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

WebSocket connections can't set custom headers from a browser, so
`/ws/files/{file_id}` takes the access token as a query parameter instead:
`wss://.../ws/files/{file_id}?token=<access_token>`.

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
| CAD | Real persistence, stub engine | sketch CRUD is real; extrude/revolve/fillet/chamfer/export return `501` |
| PCB | Real persistence, stub engine | board/component CRUD is real; DRC/ERC/Gerber/BOM export return `501` |
| AI | Real persistence, stub model | chat/message CRUD is real; assistant replies are a placeholder string, not a live model call |
| WebSocket collaboration | Real | Yjs (`y-py`) CRDT sync + presence, see below |

## Real-time collaboration

`/ws/files/{file_id}` is a per-file collaborative room. Wire format is a
custom JSON envelope (not the npm `y-websocket` binary protocol) — see
`services/backend/app/websockets/manager.py` for the exact message shapes
and the rationale. The payload inside `update` messages is a genuine Yjs
update (produced/applied via `y-py`), so multiple clients editing
concurrently merge via real CRDT semantics, not last-write-wins. Document
state persists to the `ydoc_snapshots` table when the last client in a room
disconnects, and rehydrates on the next connection.

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
