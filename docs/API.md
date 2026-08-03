# API

## Base URL

- Local: `http://localhost:8000`
- All routes are versioned under `/api/v1`.
- Interactive docs (Swagger UI) are served by FastAPI at `/docs`; the raw
  OpenAPI schema is at `/openapi.json`. `docs/architecture/api-spec.yaml` is
  the hand-written contract this implementation is converging toward —
  regenerate it from `/openapi.json` once the surface stabilizes in Phase 2.

## Authentication

Bearer JWT. Obtain a token pair from `/api/v1/auth/register` or
`/api/v1/auth/login`, then send:

```
Authorization: Bearer <access_token>
```

Access tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30 min);
use `/api/v1/auth/refresh` with the refresh token to get a new pair.

## Implemented endpoints (Step 1 scope)

| Method | Path                     | Description                     |
| ------ | ------------------------ | -------------------------------- |
| POST   | `/api/v1/auth/register`  | Create a user, returns tokens    |
| POST   | `/api/v1/auth/login`     | Authenticate, returns tokens     |
| POST   | `/api/v1/auth/refresh`   | Exchange a refresh token         |
| POST   | `/api/v1/auth/logout`    | Client-side token discard        |
| GET    | `/api/v1/auth/me`        | Current user                     |
| GET    | `/api/v1/users/me`       | Current user profile             |
| PATCH  | `/api/v1/users/me`       | Update name/avatar/settings      |
| GET    | `/api/v1/projects`       | List the current user's projects |
| POST   | `/api/v1/projects`       | Create a project                 |
| GET    | `/api/v1/projects/{id}`  | Get a project                    |
| PATCH  | `/api/v1/projects/{id}`  | Update a project                 |
| DELETE | `/api/v1/projects/{id}`  | Delete a project                 |
| GET    | `/health`                | Liveness check (unauthenticated) |

`cad`, `pcb`, `ai`, and `files` routers exist (`app/api/v1/*/routes.py`) but
still return placeholder data — real implementations land in Phase 2/3 per
`docs/architecture/roadmap.md`.

## Error format

```json
{
  "error": {
    "message": "Invalid email or password",
    "status_code": 401
  }
}
```

Validation errors (422) additionally include a `details` array with
per-field messages, matching FastAPI's default `RequestValidationError`
shape.
