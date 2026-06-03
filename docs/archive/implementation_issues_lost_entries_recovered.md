# Recovered ledger entries (ISSUE-017 through ISSUE-022)

These entries were lost from `docs/implementation_issues.md` before GitHub Issues migration.

## ISSUE-017
- Severity: Medium
- Status: open
- Evidence:
  - CLI (`src/paper_marker/cli.py`): only the root Typer app has a one-line `help=` string. Commands `list-routes`, `doctor`, and `convert` have no docstrings. All `convert` options omit Typer `help=` text, so `--help` surfaces bare parameter names with no usage guidance.
  - MCP (`src/paper_marker/mcp/server.py`): tool functions have no docstrings or parameter descriptions. Contract tests assert `description` is a string but not that it is meaningful.
  - README omits `doctor`, `--routes`, `--timeout-per-route`, valid route names, run outputs, MCP parameters, and sample MCP client configuration.
- Fix Plan:
  - Add command docstrings and per-option `help=` strings to `cli.py`.
  - Add tool and parameter docstrings in `mcp/server.py` mirroring CLI semantics.
  - Expand README with doctor, route selection, outputs, synthesis prerequisites, and MCP setup.
  - Tighten MCP contract tests for non-empty descriptions.
- Verification:
  - `paper-marker --help` and subcommand helps show descriptive text for every command and option.
  - MCP `tools/list` shows non-empty descriptions for all three tools.
  - `uv run pytest -m "not integration"` remains green.
- Done Criteria:
  - CLI and MCP self-document at the interface boundary.
  - README covers all user-facing commands, flags, outputs, and MCP setup.

## ISSUE-018
- Severity: Medium
- Status: open
- Evidence:
  - README has a short dev-focused install block; end-user PyPI install lives only in `docs/release.md`.
  - CI uses `uv sync` (editable workspace), not install-from-wheel.
  - Publish workflow builds artifacts but never installs them or validates console scripts.
  - MCP smoke check runs via `uv run paper-marker-mcp`, not installed entry points.
- Fix Plan:
  - Add dedicated Installation section (README and/or `docs/installation.md`).
  - Add install smoke test: build wheel, clean install, assert `paper-marker --help`, `list-routes`, MCP `tools/list`.
  - Wire install verification into CI (PR job or publish quality gate).
- Verification:
  - Manual: follow install doc on clean venv; both entry points work.
  - CI install-smoke job passes on PRs.
- Done Criteria:
  - End users can install and verify without reading source.
  - CI fails if console scripts or package metadata prevent install-and-run smoke.

## ISSUE-019
- Severity: High
- Status: open
- Evidence:
  - `scripts/fetch_fixtures.py` downloads PDFs only; `markdown_url` entries are ignored.
  - Integration tests write outputs to pytest `tmp_path` (discarded after run).
  - Assertions use short `golden_fragments` only.
  - Real fixture tests are opt-in and excluded from default CI.
- Fix Plan:
  - Extend catalog with `markdown_path`; update fetcher to download reference markdown.
  - Define `tests/fixtures/smoke/<fixture-id>/` layout with source, reference, and `output/`.
  - Add smoke test module and `scripts/run_smoke_fixtures.py`.
  - CI nightly/workflow: download fixtures, run smoke, upload artifacts.
- Verification:
  - Fetch materializes PDFs and reference markdowns.
  - Smoke run persists co-located artifacts.
  - CI smoke job uploads artifact bundle.
- Done Criteria:
  - Every curated catalog entry can be downloaded, converted, and inspected on disk.
  - CI runs smoke suite and preserves artifacts for review.

## ISSUE-020
- Severity: Medium
- Status: open
- Evidence:
  - CLI: `convert` treats `--out-dir` as optional with default `Path("out")`.
  - MCP: `convert_pdf_to_markdown` declares `out_dir: str = "out"`.
  - Users can convert without choosing an output location explicitly.
- Fix Plan:
  - Make `--out-dir` required on CLI (no default).
  - Remove MCP default for `out_dir`; require in tool schema.
  - Update tests, README, CHANGELOG (breaking change).
- Verification:
  - `paper-marker convert paper.pdf` without `--out-dir` fails with clear message.
  - MCP call without `out_dir` fails validation.
  - Explicit `--out-dir` path still succeeds.
- Done Criteria:
  - Neither CLI nor MCP accepts convert without explicit output directory.

## ISSUE-021
- Severity: Medium
- Status: open
- Evidence:
  - Pipeline writes `candidate_bundle/`, `final.md`, `run_report.json`, `final_result.json`.
  - CLI/MCP JSON stdout duplicates on-disk JSON files.
  - `--export-candidate-bundle` only toggles bundle subtree.
- Fix Plan:
  - Write flat `{route}.md` in `out_dir`; optional `synthesized.md` when `--synthesize`.
  - Keep structured metadata in CLI/MCP JSON response only.
  - Remove or repurpose `export_candidate_bundle`.
  - Document failure = no markdown file; defer assets to ISSUE-022.
- Verification:
  - Two-route convert yields only `{route}.md` files (+ `synthesized.md` if requested).
  - No `candidate_bundle/`, `run_report.json`, or `final_result.json` by default.
  - JSON responses still include candidate statuses and selection metadata.
- Done Criteria:
  - Default disk output is flat: one markdown per successful route, optional synthesized.md.
  - Edge cases documented and tested.

## ISSUE-022
- Severity: Medium
- Status: open
- Evidence:
  - Routes (Marker, MinerU) write figures under `_work/`; pipeline copies markdown text only.
  - `CandidateResult.assets` is never populated.
  - Lean `{route}.md` in `out_dir` breaks relative image links without `--keep-temp`.
- Fix Plan:
  - Discover non-markdown outputs after each route run; populate `CandidateResult.assets`.
  - Copy assets to `out_dir` (e.g. `{route}_assets/`).
  - Rewrite relative image/link paths in `{route}.md`.
  - Add unit tests with synthetic `_work/` trees; figure-heavy smoke fixture.
- Verification:
  - Figure-heavy PDF: `out_dir/marker.md` renders images without `--keep-temp`.
  - JSON response lists copied asset paths.
- Done Criteria:
  - Portable `{route}.md` renders figures correctly for asset-emitting routes.
  - Asset layout documented; ISSUE-021 lean layout preserved.
