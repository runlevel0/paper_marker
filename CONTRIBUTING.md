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

We use a file-based ledger at `docs/implementation_issues.md` instead of GitHub Issues.

When you start work on a tracked item, set its status to `in_progress`. When finished, set it to `done` and fill in **Evidence** and **Verification** (commands run and results).

If you discover a new gap, add `ISSUE-NNN` following the existing format rather than expanding unrelated fixes in the same change.

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
