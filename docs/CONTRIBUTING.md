# Contributing

## Before you start

1. Read [SETUP.md](SETUP.md) and get the stack running locally.
2. Read [CODING_STANDARDS.md](CODING_STANDARDS.md) for style and structure.
3. Read [GIT_WORKFLOW.md](GIT_WORKFLOW.md) for branching and PR conventions.

## Pre-commit hooks

This repo uses [pre-commit](https://pre-commit.com) to run formatters and
linters before each commit:

```bash
pip install pre-commit
pre-commit install
```

`black`, `isort`, and `flake8` run against `services/backend/`; `eslint` and
`prettier` run against changed frontend files.

## Making a change

1. Branch off `main`: `git checkout -b feature/my-change`.
2. Make the change, with tests where [CODING_STANDARDS.md](CODING_STANDARDS.md#testing-expectations) calls for them.
3. Run the relevant test suite locally (`pytest` for backend, `pnpm --filter web run build` for frontend) before opening a PR.
4. Open a PR using the template; fill in the test plan honestly.

## Reporting bugs / requesting features

Use the issue templates under `.github/ISSUE_TEMPLATE/`.
