# Backend service

FastAPI + SQLAlchemy 2.0 + Alembic backend for Enginex AI.

## Structure

- `app/main.py` — app entry point, CORS, error handlers, router registration
- `app/config.py` — `Settings` (env-driven, `pydantic-settings`)
- `app/database.py` — SQLAlchemy engine/session, `Base`, `get_db` dependency
- `app/models/` — SQLAlchemy ORM models (one file per domain area)
- `app/api/v1/<domain>/` — `routes.py` + `schemas.py` + `service.py` (+
  `dependencies.py` for auth) per domain: `auth`, `users`, `projects` are
  fully implemented; `cad`, `pcb`, `ai`, `files` are placeholders for
  Phase 2/3
- `app/utils/security.py` — JWT + bcrypt password hashing
- `app/middleware/error_handler.py` — global exception → JSON error mapping
- `migrations/` — Alembic; `versions/001_initial_schema.py` is the initial
  schema
- `tests/unit`, `tests/integration` — pytest suite (SQLite in-memory DB via
  `tests/conftest.py`, no external services required)

## Running

```bash
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env      # point DATABASE_URL at a reachable Postgres
alembic upgrade head
uvicorn app.main:app --reload
```

## Testing

```bash
pytest
```

Tests spin up an isolated in-memory SQLite database per test via
`tests/conftest.py` — no Docker or running Postgres instance required.
