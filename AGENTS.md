# AGENTS.md

Guidance for AI agents (and humans) working in this repository. Read this before making changes.

## What this project is

`paper-marker` is a local-first scientific **PDF -> Markdown** converter.

- Runs multiple external converter CLIs **in parallel** (`ProcessPoolExecutor`), scores the
  candidate outputs heuristically, and selects a "best guess".
- Optionally **synthesizes** a merged result via an OpenRouter/OpenAI-compatible API.
- Exposes both a **Typer CLI** (`paper-marker`) and a **stdio MCP server** (`paper-marker-mcp`).

Routes call **external command-line tools** (`marker`, `magic-pdf`, `nougat`, `markitdown`),
not in-process Python APIs. A route is only "available" if its CLI is found on `PATH`.

## Environment & commands

- **Shell is PowerShell on Windows.** Do not use bash syntax. Quote paths with spaces.
- **Packaging/deps is `uv`** (`pyproject.toml` + `uv.lock`). Do not add a `requirements.txt`
  or `setup.py`.
- To run Python, use the project environment. Prefer `uv run ...` so the venv is used
  automatically; otherwise activate `.venv` first.

```powershell
uv sync --extra llm            # dev install with synthesis support
uv sync --extra all --extra llm # include all route extras
uv run pytest -m "not integration"  # default test run (what CI runs)
uv run ruff check .
uv run ruff format --check .
```

## Code conventions

- Target **Python 3.11+**. Keep `from __future__ import annotations` at the top of modules.
- **Type hints are required** on public functions/methods.
- **Ruff** is the linter/formatter: line length 100, rules `E,F,I,UP,B,SIM`, `target-version = py311`.
  Use ruff formatting style. There is no Black/mypy/pyright configured yet (type checking is a tracked gap).
- When using matplotlib (if ever needed), prefer the object-oriented API.
- Keep imports at the top of files; avoid inline imports.

## Architecture map

- `src/paper_marker/cli.py` — Typer CLI (`list-routes`, `doctor`, `convert`).
- `src/paper_marker/mcp/server.py` — MCP tools; **keep parity with the CLI** (e.g. `keep_temp`,
  candidate-bundle flags).
- `src/paper_marker/core/pipeline.py` — `ConversionOrchestrator`: validates routes, fans out to
  workers, scores, optionally synthesizes, writes outputs.
- `src/paper_marker/core/models.py` — domain/result payloads (dataclasses).
- `src/paper_marker/config.py` — `AppSettings` (Pydantic Settings, reads `.env` + env vars).
- `src/paper_marker/routes/` — one module per converter CLI; all implement
  `ConversionRoute` (`base.py`) with `is_available()` and `convert()`.
- `src/paper_marker/synthesis/openrouter_synth.py` — LLM synthesis over httpx.

**Outputs of a run:** flat `{route}.md` per successful route, optional `synthesized.md`
when synthesizing, `_work/` only with `--keep-temp`. Run metadata is CLI/MCP JSON only.

## Modeling policy (important)

Per `docs/modeling_policy.md`:
- **Pydantic** is for configuration/env parsing only (`config.py`).
- **Dataclasses** are for runtime domain/result payloads (`core/models.py`), serialized via
  explicit `to_json_dict()`.
- Add new runtime payloads as dataclasses unless an external schema demands Pydantic at a boundary.

## Testing

- `pytest`; `pythonpath = ["src"]`. Tests live in `tests/unit/` and `tests/integration/`.
- The `integration` marker gates heavy/real-converter tests. **CI runs `-m "not integration"`**,
  so the real fixture matrix does not run by default.
- The real fixture matrix (`tests/integration/test_real_fixture_matrix.py`) needs the env var
  `PAPER_MARKER_FIXTURE_CATALOG`, downloaded PDFs, and the converter CLIs installed.
  **No PDF binaries are committed** — only JSON catalogs under `tests/fixtures/`.
- Route-level and synthesis-HTTP tests are currently missing (tracked as GitHub issue #10).

## Issue tracking workflow

This project tracks work in **GitHub Issues**: https://github.com/runlevel0/paper_marker/issues

- Legacy migrated items use `[ISSUE-NNN]` in titles; see [`docs/archive/github_issue_map.json`](docs/archive/github_issue_map.json).
- Open new tasks via the [implementation task template](https://github.com/runlevel0/paper_marker/issues/new?template=implementation_task.yml).
- When starting work, assign yourself and add labels as needed; close with evidence in comments or the PR (`Fixes #N`).
- PRs should reference the GitHub issue they address.

**Agent commands (requires `gh auth login` or `GH_TOKEN`):**

```powershell
gh issue list --state open --repo runlevel0/paper_marker
gh issue view 17 --repo runlevel0/paper_marker
gh issue create --repo runlevel0/paper_marker --title "..." --body "..."
```

Historical markdown ledger archives live under `docs/archive/`; see [`docs/implementation_issues.md`](docs/implementation_issues.md) for pointers.

## Known gotchas

- **Do not commit build artifacts:** `*.egg-info/` and `build/` are gitignored; run `uv build`
  locally without committing those outputs.
- **PyPI metadata** — `LICENSE`, `license`, authors, classifiers, and `[project.urls]` are in `pyproject.toml`; bump version and tag per `docs/release.md` before publishing.
- **Windows + `ProcessPoolExecutor`:** workers re-import the package and use spawn semantics; keep
  worker arguments picklable (current code passes strings/paths). Heavy ML deps make worker startup slow.
- **Folder name `resources/`** is canonical (ISSUE-016 resolved).

## Configuration / environment variables

Read by `AppSettings` in `config.py` (also loadable from a `.env` file):

- `OPENROUTER_API_KEY` / `OPENAI_API_KEY` — synthesis credentials (either works).
- `OPENAI_BASE_URL` — default `https://openrouter.ai/api/v1`.
- `PAPER_MARKER_OPENROUTER_MODEL` — default model (`openrouter/auto`).
- `PAPER_MARKER_TIMEOUT_PER_ROUTE` — per-route timeout seconds (default 300).
- `PAPER_MARKER_MAX_PARALLEL_ROUTES` — worker cap (default 4).
- `PAPER_MARKER_SYNTH_MAX_CHARS_PER_CANDIDATE` — prompt budget per candidate (default 12000).
- `PAPER_MARKER_SYNTH_MAX_TOTAL_CHARS` — total prompt budget (default 30000).
