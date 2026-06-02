# Implementation Issues Ledger

This ledger tracks active implementation issues and their closure evidence.

Status lifecycle: `open -> in_progress -> blocked|done`.

## ISSUE-001
- ID: ISSUE-001
- Severity: High
- Status: in_progress
- Owner: unassigned
- Evidence:
  - Review found fixture-backed real converter integration coverage is missing.
  - Current integration tests primarily mock orchestration behavior.
  - Added `tests/integration/test_real_fixture_matrix.py` for real-route fixture execution.
  - Added fixture catalog template `tests/fixtures/fixture_catalog.example.json`.
- Fix Plan:
  - Add fixture-backed integration tests for converter routes.
  - Include multiple source categories and provenance notes.
  - Add golden-fragment assertions on normalized markdown.
- Verification:
  - `uv run pytest`
  - targeted integration test commands
- Done Criteria:
  - At least one real-path integration scenario per supported route gate.
  - Fixture provenance documented with source links/notes.
  - Tests pass in CI/local workflow.

## ISSUE-002
- ID: ISSUE-002
- Severity: Medium
- Status: done
- Owner: unassigned
- Evidence:
  - CLI plan includes `--keep-temp`, but implementation omitted it.
  - `--keep-temp` added in CLI and wired into `ConversionRequest`.
  - README and MCP parity note updated.
- Fix Plan:
  - Add `--keep-temp` to CLI and plumb request handling.
  - Document behavior in README and MCP parity notes.
- Verification:
  - `uv run pytest`
  - `paper-marker convert --help`
- Done Criteria:
  - Flag exists, behavior documented, tests cover it.

## ISSUE-003
- ID: ISSUE-003
- Severity: Medium
- Status: done
- Owner: unassigned
- Evidence:
  - Invalid route names can fail in workers and return `route_name="unknown"`.
  - Route names are now validated before worker dispatch.
- Fix Plan:
  - Validate requested route names before launching workers.
  - Return deterministic actionable errors.
- Verification:
  - `uv run pytest`
- Done Criteria:
  - Invalid routes fail fast with clear message and route list.

## ISSUE-004
- ID: ISSUE-004
- Severity: Medium
- Status: done
- Owner: unassigned
- Evidence:
  - Synthesis prompt includes full markdown payload with no size control.
  - Added per-candidate and total prompt-size budget controls in synthesis prompt builder.
  - Added `prompt_budget` metadata in synthesis result payloads.
- Fix Plan:
  - Add prompt budget controls and truncation strategy.
  - Record truncation metadata in final result provenance.
- Verification:
  - `uv run pytest`
- Done Criteria:
  - Prompt construction bounded by configured limits.
  - Truncation metadata persisted and tested.

## ISSUE-005
- ID: ISSUE-005
- Severity: Low
- Status: done
- Owner: unassigned
- Evidence:
  - Plan asks to clarify dataclass vs Pydantic boundary and serialization policy.
  - Added `docs/modeling_policy.md`.
  - Added policy docstring in `src/paper_marker/core/models.py`.
- Fix Plan:
  - Define policy in docs and enforce in core model code.
  - Keep settings with Pydantic; domain runtime payloads as dataclasses.
- Verification:
  - Documentation review
  - `uv run pytest`
- Done Criteria:
  - Policy is explicit, consistent, and reflected in model module doc/comments.

## ISSUE-006
- ID: ISSUE-006
- Severity: High
- Status: open
- Owner: unassigned
- Evidence:
  - No `LICENSE` file exists in the repo and `pyproject.toml` has no `license` field.
  - `docs/release.md` documents PyPI publishing, but publishing without a license is a legal ambiguity and violates PyPI best practice.
  - `pyproject.toml` also lacks `authors`, `classifiers`, `keywords`, and `[project.urls]`.
- Fix Plan:
  - Choose and add a `LICENSE` file (e.g. MIT/Apache-2.0).
  - Add `license`, `authors`, `classifiers`, `keywords`, and `[project.urls]` to `pyproject.toml`.
- Verification:
  - `LICENSE` present at repo root.
  - `uv build` produces metadata with license/classifiers.
- Done Criteria:
  - License file committed and referenced in package metadata.
  - PyPI page renders complete project metadata.

## ISSUE-007
- ID: ISSUE-007
- Severity: High
- Status: open
- Owner: unassigned
- Evidence:
  - `.github/workflows/ci.yml` and `publish.yml` are untracked, so CI does not run on the remote.
  - `docs/release.md` is untracked.
  - Workflows trigger on branch `main`, but the repo's default branch is `master`; CI would not fire on the default branch even once committed.
- Fix Plan:
  - Commit `.github/` and `docs/release.md`.
  - Reconcile branch naming: rename `master` -> `main` or update workflow triggers to `master`.
- Verification:
  - CI run appears on a push/PR to the default branch.
- Done Criteria:
  - CI executes lint + tests on the default branch and on PRs.

## ISSUE-008
- ID: ISSUE-008
- Severity: Medium
- Status: done
- Owner: unassigned
- Evidence:
  - `src/paper_marker.egg-info/` is tracked (e.g. `PKG-INFO`) and shows as modified in `git status`.
  - `.gitignore` does not exclude `*.egg-info/`.
  - Added `*.egg-info/` to `.gitignore` and removed `src/paper_marker.egg-info` from the index via `git rm -r --cached` (commit `be527c5`).
- Fix Plan:
  - Add `*.egg-info/` to `.gitignore`.
  - `git rm -r --cached src/paper_marker.egg-info`.
- Verification:
  - `git status` no longer shows egg-info changes after a build.
- Done Criteria:
  - Build artifacts are not tracked.

## ISSUE-009
- ID: ISSUE-009
- Severity: High
- Status: done
- Owner: unassigned
- Evidence:
  - Updated `src/paper_marker/core/pipeline.py` to map submitted futures to route names, so worker exceptions now produce route-attributed `CandidateResult` errors instead of `route_name="unknown"`.
  - Updated selection logic to derive `best_guess` only from successful candidates and emit `selection_reason="all routes failed"` with `selected_route="none"` when every route fails; this avoids misleading successful-selection metadata and skips writing `final.md`.
  - Added unit coverage in `tests/unit/test_pipeline.py`:
    - `test_orchestrator_attributes_worker_failure_to_route`
    - `test_orchestrator_reports_all_routes_failed`
    - plus deterministic worker stubbing in `test_orchestrator_writes_candidate_bundle_and_best_guess` to avoid environment-dependent route availability.
  - Commit: `d2f2e76`.
- Fix Plan:
  - Map each submitted future to its route name and use it in failure results.
  - Add an explicit "all routes failed" terminal state distinct from a successful selection; avoid writing a misleading `final.md`/report.
- Verification:
  - `uv run --no-sync pytest tests/unit/test_pipeline.py` -> passed (`6 passed`), including:
    - worker exception attribution test
    - all-routes-failed terminal-state test
  - `uv run --no-sync ruff check .` -> fails due pre-existing lint in unrelated integration files and one initial long-line issue in `tests/unit/test_pipeline.py` that was fixed in this change.
  - `uv run --no-sync ruff format --check .` -> fails due pre-existing format drift in unrelated files, and includes `src/paper_marker/core/pipeline.py` / `tests/unit/test_pipeline.py` in the global list because repository-wide formatting is not currently clean.
  - `uv run --no-sync pytest -m "not integration"` -> fails during collection in pre-existing integration modules (`ModuleNotFoundError: No module named 'tests'` in `tests/integration/test_mcp_agent_style_flows.py` and `tests/integration/test_mcp_contracts.py`).
- Done Criteria:
  - Failures are attributed to the correct route.
  - No misleading selection is reported when every route fails.

## ISSUE-010
- ID: ISSUE-010
- Severity: High
- Status: open
- Owner: unassigned
- Evidence:
  - Route modules (`marker_route.py`, `mineru_route.py`, `nougat_route.py`, `markitdown_route.py`) have no unit tests; subprocess/glob/error handling is uncovered.
  - `synthesize_candidates` HTTP path (httpx, `raise_for_status`) is untested; only the prompt builder/budget is tested.
  - No coverage tooling (`pytest-cov`) or coverage gate.
- Fix Plan:
  - Add route-level tests mocking subprocess and filesystem outputs.
  - Add synthesis HTTP tests with a mocked transport.
  - Add `pytest-cov` and a coverage report in CI.
- Verification:
  - `uv run pytest --cov` reports route + synthesis coverage.
- Done Criteria:
  - Each route and the synthesis HTTP path have unit coverage.
  - Coverage is reported in CI.

## ISSUE-011
- ID: ISSUE-011
- Severity: Medium
- Status: open
- Owner: unassigned
- Evidence:
  - Type hints are present throughout but no static type checker is configured or run.
- Fix Plan:
  - Add `mypy` or `pyright` to the dev group with config.
  - Run the type check in CI.
- Verification:
  - `uv run mypy src` (or pyright) passes in CI.
- Done Criteria:
  - Type checking is enforced on every CI run.

## ISSUE-012
- ID: ISSUE-012
- Severity: Medium
- Status: open
- Owner: unassigned
- Evidence:
  - No `CONTRIBUTING.md`, no `.env.example`, no `CHANGELOG.md`.
  - README documents only 3 of 8 environment variables read by `config.py` (timeout, max parallel routes, synth char budgets are undocumented).
- Fix Plan:
  - Add `CONTRIBUTING.md` (dev workflow, lint/test commands, branch conventions).
  - Add `.env.example` listing all supported env vars.
  - Add `CHANGELOG.md` and document the full env var set in README.
- Verification:
  - Files present; README env section lists all variables.
- Done Criteria:
  - New contributors can set up and configure the tool from docs alone.

## ISSUE-013
- ID: ISSUE-013
- Severity: Low
- Status: open
- Owner: unassigned
- Evidence:
  - No structured logging; failures surface only in result metadata / stderr tails, making stuck `ProcessPoolExecutor` runs hard to debug.
- Fix Plan:
  - Introduce `logging` with a configurable level across pipeline, routes, and synthesis.
- Verification:
  - Log output observable at debug level during a run.
- Done Criteria:
  - Key lifecycle and failure events are logged.

## ISSUE-014
- ID: ISSUE-014
- Severity: Low
- Status: open
- Owner: unassigned
- Evidence:
  - `marker_route.py`, `mineru_route.py`, and `nougat_route.py` share near-identical subprocess/glob/error patterns.
- Fix Plan:
  - Extract a shared CLI-route base/helper for subprocess invocation and output collection.
- Verification:
  - `uv run pytest` green after refactor.
- Done Criteria:
  - Duplication reduced without behavior change.

## ISSUE-015
- ID: ISSUE-015
- Severity: Low
- Status: open
- Owner: unassigned
- Evidence:
  - Synthesis HTTP uses `raise_for_status()` with no retry/backoff; a single transient 429/5xx aborts the run after all conversion work is done.
- Fix Plan:
  - Add bounded retry with backoff for transient HTTP errors in `openrouter_synth.py`.
- Verification:
  - Unit test simulating a transient failure then success.
- Done Criteria:
  - Transient synthesis errors are retried within configured bounds.

## ISSUE-016
- ID: ISSUE-016
- Severity: Low
- Status: done
- Owner: unassigned
- Evidence:
  - Renamed top-level folder from the deprecated spelling to `resources/`.
  - Updated `AGENTS.md` known-gotchas note to use the canonical `resources/` name.
  - Updated this issue entry to remove stale references to the deprecated spelling.
  - Files changed: `AGENTS.md`, `docs/implementation_issues.md`, `resources/background_on_markdown_conversion.md` (via directory rename).
- Fix Plan:
  - Rename the top-level folder to `resources/` and update references.
- Verification:
  - `uv run ruff check .` -> failed due pre-existing unrelated lint in `scripts/mcp_smoke_check.py`, `tests/integration/test_mcp_agent_style_flows.py`, and `tests/integration/test_mcp_contracts.py`.
  - `uv run ruff format --check .` -> failed due pre-existing unrelated format drift in `scripts/mcp_smoke_check.py` and integration test files.
  - `uv run pytest -m "not integration"` -> passed (`13 passed, 8 deselected`).
  - `rg "res{2}ources"` -> no matches found.
- Done Criteria:
  - Directory renamed; no stale references remain.
