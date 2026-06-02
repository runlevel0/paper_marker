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

**Outputs of a run:** `final.md`, `final_result.json`, `run_report.json`, optional
`candidate_bundle/`, and `_work/` (kept only with `--keep-temp`).

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
- Route-level and synthesis-HTTP tests are currently missing (tracked as ISSUE-010).

## Issue tracking workflow

This repo uses a file-based ledger instead of GitHub issues: **`docs/implementation_issues.md`**.

- Status lifecycle: `open -> in_progress -> blocked|done`.
- When you start work, set the issue to `in_progress`; when done, set `done` and fill in
  **Evidence** (what changed) and **Verification** (commands run).
- Add new findings as `ISSUE-NNN` following the existing format (ID, Severity, Status, Owner,
  Evidence, Fix Plan, Verification, Done Criteria).

## Known gotchas

- **Branch/CI mismatch:** repo default branch is `master`, but `.github/workflows/*` trigger on
  `main` and are currently **untracked** — CI does not run yet (ISSUE-007).
- **Do not commit build artifacts:** `src/paper_marker.egg-info/` is currently tracked by mistake;
  it should be gitignored (ISSUE-008).
- **No `LICENSE`** and thin `pyproject.toml` metadata — do not publish to PyPI until fixed (ISSUE-006).
- **Windows + `ProcessPoolExecutor`:** workers re-import the package and use spawn semantics; keep
  worker arguments picklable (current code passes strings/paths). Heavy ML deps make worker startup slow.
- **Worker failure attribution:** crashed futures are currently mislabeled `route_name="unknown"`,
  and a run with all routes failing still reports a misleading "best guess" (ISSUE-009).
- **Folder name `ressources/`** is a known misspelling (ISSUE-016).

## Configuration / environment variables

Read by `AppSettings` in `config.py` (also loadable from a `.env` file):

- `OPENROUTER_API_KEY` / `OPENAI_API_KEY` — synthesis credentials (either works).
- `OPENAI_BASE_URL` — default `https://openrouter.ai/api/v1`.
- `PAPER_MARKER_OPENROUTER_MODEL` — default model (`openrouter/auto`).
- `PAPER_MARKER_TIMEOUT_PER_ROUTE` — per-route timeout seconds (default 300).
- `PAPER_MARKER_MAX_PARALLEL_ROUTES` — worker cap (default 4).
- `PAPER_MARKER_SYNTH_MAX_CHARS_PER_CANDIDATE` — prompt budget per candidate (default 12000).
- `PAPER_MARKER_SYNTH_MAX_TOTAL_CHARS` — total prompt budget (default 30000).
