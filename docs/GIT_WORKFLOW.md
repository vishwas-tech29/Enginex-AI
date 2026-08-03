# Git workflow

## Branches

- `main` — always deployable. Protected; merges only via reviewed PR.
- `develop` — integration branch for the next release, if/when the team
  needs a staging cut separate from `main`.
- `feature/<short-description>` — new work, branched from `main` (or
  `develop` once it exists).
- `hotfix/<short-description>` — urgent production fixes, branched from
  `main`, merged back to `main` (and `develop` if in use).

## Commits

- Small, focused commits over one giant diff.
- Prefer imperative mood: "Add project delete endpoint", not "Added" or
  "Adding".

## Pull requests

- Use the PR template (`.github/PULL_REQUEST_TEMPLATE.md`).
- Link the issue it closes.
- CI must pass (`ci-backend.yml` / `ci-frontend.yml` as relevant) before
  requesting review.
- Squash-merge by default to keep `main` history linear; use a merge commit
  only for long-lived feature branches with meaningful sub-history.

## Releases

- Tag `vX.Y.Z` on `main` to trigger `cd-deploy.yml`, which builds and pushes
  backend/frontend images to GHCR. Cluster deployment is a manual step until
  Phase 5 wires up GitOps/kubectl in CI.
