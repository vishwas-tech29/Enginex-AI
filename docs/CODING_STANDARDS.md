# Coding standards

## TypeScript (apps/web, packages/*)

- Strict mode is on (`tsconfig.json`); don't weaken it per-file.
- No `any` — if a type is genuinely unknown, use `unknown` and narrow it.
- Path alias `@/*` maps to `apps/web/src/*` — prefer it over relative `../../..` imports.
- Components: one component per file, named exports for anything reused,
  default export only for Next.js pages.
- Server calls go through `src/services/api/*` — components should not call
  `axios`/`fetch` directly.
- State: Zustand (`src/store/*`) for cross-page app state, component state
  for anything local/transient. Don't put server data that TanStack Query
  can own into Zustand.

## Python (services/backend)

- Type hints on all function signatures.
- Formatting: `black` (100 char line length) + `isort` (`black` profile).
  Both run in pre-commit and CI — don't hand-format around them.
- Route handlers stay thin: validate via Pydantic schema, delegate to a
  `service.py` class, return a response model. Business logic and DB queries
  belong in the service layer, not the route function.
- Each `api/v1/<module>/` follows the same four-file shape: `routes.py`,
  `schemas.py`, `service.py`, and (only where auth state is needed)
  `dependencies.py`.
- Raise `HTTPException` from services for expected error cases (404, 409,
  etc.) — don't let route handlers do error translation.

## Folder structure rules

- New frontend features that are more than a page + a couple of components
  go under `src/modules/<feature>/` (see `cad-editor`, `pcb-editor`,
  `ai-chat`) with `components/`, `hooks/`, `store/`, `services/`, `types/`.
- New backend domains follow `app/api/v1/<domain>/` for the HTTP surface and
  `app/models/<domain>.py` for persistence.

## Testing expectations

- Backend: every new service method that touches the database gets at least
  one integration test in `tests/integration/`; pure functions (validators,
  security helpers) get unit tests in `tests/unit/`.
- Frontend: components with non-trivial logic (forms, stores) get a test
  under a co-located `__tests__/` or `*.test.tsx` file once Jest is wired up
  for a given module — not required for pure presentational components.
- CI (`ci-backend.yml`, `ci-frontend.yml`) must stay green; a red CI blocks
  merge.
