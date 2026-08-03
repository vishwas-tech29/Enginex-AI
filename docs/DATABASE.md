# Database

PostgreSQL 15. Schema source of truth is the SQLAlchemy models under
`services/backend/app/models/`; the Alembic migration in
`services/backend/migrations/versions/001_initial_schema.py` creates the
initial schema from those models. `docs/architecture/database-schema.sql` is
the original design reference this migration was derived from — if the two
ever diverge, the migration (and the models it comes from) is authoritative.

## Entity overview

```text
users ──< organizations (owner_id)
organizations ──< teams
organizations ──< projects
teams ──< projects (nullable)
users ──< projects (owner_id)
projects ──< folders (self-referencing tree via parent_id)
projects ──< files
folders ──< files (nullable)
files ──< cad_objects (self-referencing tree via parent_id)
files ──< pcb_boards ──< pcb_components
files ──< layers
users ──< ai_chats
projects ──< ai_chats (nullable)
ai_chats ──< ai_messages
ai_agents ──< agent_memory
ai_chats ──< agent_memory (nullable)
organizations ──< subscriptions
users ──< api_keys
organizations ──< usage_logs
users ──< audit_logs (nullable)
```

`──<` denotes a one-to-many relationship (parent ──< children).

## Notable design choices

- All primary keys are UUIDs (`uuid_generate_v4()`), generated app- or
  DB-side depending on path — safe for multi-region and offline-first client
  scenarios later on.
- Design-specific payloads (`cad_objects.data`, `pcb_boards.data`,
  `pcb_components.data`) are JSONB rather than fully normalized columns,
  since CAD/PCB geometry schemas will evolve quickly in Phase 2+.
- `ai_messages.tool_calls` is JSONB for the same reason — tool call shapes
  will change as the agent/tool registry (see
  `docs/architecture/ai-agents.md`) grows.
- Soft-delete only exists on `files` (`is_deleted`); everything else uses
  hard deletes with `ON DELETE CASCADE`/`SET NULL` as appropriate. Revisit
  this if audit requirements demand soft-delete elsewhere.

## Indexes

Defined in the initial migration: `files.project_id`,
`projects.organization_id`, `cad_objects.file_id`, `ai_messages.chat_id`,
`agent_memory.agent_id`, `usage_logs(organization_id, created_at)`,
`audit_logs(user_id, created_at)`. Add more as query patterns emerge — don't
speculatively index columns that aren't filtered/joined on yet.
