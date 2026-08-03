#!/usr/bin/env bash
# Apply database migrations against the running backend container.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

docker compose exec -T backend alembic upgrade head
