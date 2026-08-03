# Web application

Next.js 14 (Pages Router) + TypeScript + Tailwind CSS frontend for Enginex AI.

## Structure

- `src/pages` — routes (`login`, `register`, `dashboard/*`, etc.)
- `src/components` — `common/` (Button, Card, Modal, Navbar, Sidebar),
  `auth/` (forms, `ProtectedRoute`), `layout/` (`AppLayout`, `AuthLayout`,
  `DashboardLayout`)
- `src/modules` — larger features (`cad-editor`, `pcb-editor`, `ai-chat`),
  each with its own `components/`, `store/`, `services/`
- `src/services/api` — typed API clients (`client.ts` has the Axios instance
  + interceptors; `auth.ts`, `projects.ts` wrap specific endpoints)
- `src/store` — Zustand stores (`authStore`, `projectStore`, `uiStore`)
- `src/types` — shared TypeScript types mirroring the backend schemas

## Running

From the repo root (this is a pnpm workspace):

```bash
pnpm install
pnpm --filter web dev
```

Requires `NEXT_PUBLIC_API_URL` pointing at a running backend — see
`.env.local.example`.
