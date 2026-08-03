#!/usr/bin/env bash
# Initial local development setup for Enginex AI.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

echo "== Checking system requirements =="
for cmd in docker node python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd" >&2
    exit 1
  fi
done

if ! command -v pnpm >/dev/null 2>&1; then
  echo "pnpm not found — enabling via corepack"
  corepack enable
  corepack prepare pnpm@9.0.0 --activate
fi

echo "== Creating env files from examples =="
[ -f .env ] || cp .env.example .env
[ -f apps/web/.env.local ] || cp apps/web/.env.local.example apps/web/.env.local
[ -f services/backend/.env ] || cp services/backend/.env.example services/backend/.env

echo "== Installing frontend dependencies =="
pnpm install

echo "== Starting Docker Compose =="
docker compose up -d --build

echo "== Waiting for backend to become healthy =="
until curl -sf http://localhost:8000/health >/dev/null 2>&1; do
  sleep 2
done

echo "== Running database migrations =="
"$repo_root/infrastructure/scripts/migrate.sh"

echo "== Seeding test data =="
"$repo_root/infrastructure/scripts/seed.sh"

cat <<'EOF'

Setup complete.
  Frontend: http://localhost:3000
  Backend:  http://localhost:8000/docs
  RabbitMQ: http://localhost:15672 (guest/guest)

EOF
