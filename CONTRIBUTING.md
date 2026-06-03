# Contributing to paper-marker

Thank you for helping improve `paper-marker`. This guide covers local setup, day-to-day commands, and how we track work.

## Prerequisites

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/) for dependency management
- On Windows, use **PowerShell** (not bash) when running the commands below

## Local setup

Clone the repository and install dependencies:

```powershell
uv sync --extra llm
```

For all converter route extras (heavy ML dependencies):

```powershell
uv sync --extra all --extra llm
```

Copy `.env.example` to `.env` and fill in any API keys you need for synthesis or integration tests.

## Development commands

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest -m "not integration"
```

The `integration` marker gates real-converter and MCP protocol tests. CI runs only `-m "not integration"`.

Optional checks:

```powershell
uv run paper-marker list-routes
uv run paper-marker doctor
```

## Branch conventions

- Default branch: `main`
- Open pull requests against `main`
- CI runs lint, format check, and unit tests on pull requests and pushes to `main`

## Issue tracking

We use **GitHub Issues**: https://github.com/runlevel0/paper_marker/issues

- Open new implementation tasks with the [implementation task template](https://github.com/runlevel0/paper_marker/issues/new?template=implementation_task.yml).
- Migrated legacy items are titled `[ISSUE-NNN]`; mapping is in `docs/archive/github_issue_map.json`.
- When you start work, assign the issue and comment with your plan; when finished, close via PR (`Fixes #N`) with **Evidence** and **Verification** (commands run).
- Do not add new items to the old markdown ledger; see `docs/implementation_issues.md` for archive pointers only.

```powershell
gh issue list --state open --repo runlevel0/paper_marker
gh issue view 17 --repo runlevel0/paper_marker
```

## Code conventions

See `AGENTS.md` for architecture, modeling policy, and agent-oriented gotchas. In short:

- Type hints on public functions and methods
- Ruff formatting (line length 100)
- `from __future__ import annotations` at the top of modules
- Pydantic for config (`config.py`); dataclasses for runtime payloads (`core/models.py`)
- Keep CLI and MCP server behavior in parity when changing shared options

## Tests

- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/` (marker `integration`)

Real fixture-matrix tests require `PAPER_MARKER_FIXTURE_CATALOG`, downloaded PDFs, and converter CLIs on `PATH`. See `tests/fixtures/README.md`.

## Pull requests

1. Run `ruff check`, `ruff format --check`, and `pytest -m "not integration"` locally
2. Keep changes scoped to the issue or feature you are addressing
3. Do not commit build artifacts (for example `*.egg-info/`)
