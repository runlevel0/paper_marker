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
