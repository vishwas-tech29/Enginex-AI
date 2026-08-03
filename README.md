# Enginex AI

An AI-native engineering platform for CAD, PCB design, simulation, and
collaboration. This repo is a pnpm/Turborepo monorepo: a Next.js web app, a
FastAPI backend, and shared TypeScript packages.

## Status

**Step 1 — Foundation** is complete: monorepo scaffold, database schema +
migration, Docker Compose dev environment, working auth (register/login/JWT),
and CI. See [docs/architecture/roadmap.md](docs/architecture/roadmap.md) for
what's next.

## Tech stack

- **Frontend:** Next.js 14, React 18, TypeScript (strict), Tailwind CSS, Zustand, TanStack Query
- **Backend:** FastAPI, Python 3.11, SQLAlchemy 2.0, Pydantic v2, Alembic
- **Data:** PostgreSQL 15, Redis 7, RabbitMQ 3
- **Tooling:** pnpm workspaces + Turborepo, Docker Compose, GitHub Actions

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Frontend at http://localhost:3000, backend at http://localhost:8000 (Swagger
UI at `/docs`). Full instructions, native (non-Docker) setup, and
troubleshooting: [docs/SETUP.md](docs/SETUP.md).

## Repository layout

```
apps/web/            Next.js frontend
services/backend/    FastAPI backend
packages/types/       Shared TypeScript types
packages/utils/        Shared TypeScript utilities
deployments/k8s/      Kubernetes manifests (production reference)
docs/architecture/    Architecture blueprint (system design, schema, roadmap)
docs/                 Practical guides: setup, standards, git workflow, API, DB
```

## Documentation

- [Architecture blueprint](docs/architecture/complete-architecture.md) — system design, AI layer, deployment, security
- [Development roadmap](docs/architecture/roadmap.md)
- [Setup guide](docs/SETUP.md)
- [Database reference](docs/DATABASE.md)
- [API reference](docs/API.md)
- [Coding standards](docs/CODING_STANDARDS.md)
- [Git workflow](docs/GIT_WORKFLOW.md)
- [Contributing](docs/CONTRIBUTING.md)
