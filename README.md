# paper-marker

Local-first scientific PDF to Markdown converter with:
- parallel route execution (Marker, MinerU, Nougat, MarkItDown fallback)
- optional OpenRouter/OpenAI-compatible synthesis
- both CLI and stdio MCP server interfaces

## Installation with uv

Project-local development:

```powershell
uv sync --extra llm
```

Install with all route extras:

```powershell
uv sync --extra all --extra llm
```

User-space global install (tool mode):

```powershell
uv tool install ".[all,llm]"
```

Route CLIs installed as dependencies of the tool (for example `marker`, `magic-pdf`) are
discovered automatically from the tool environment; you do not need to add the uv tool
`Scripts` directory to `PATH`.

## CLI

List available routes:

```powershell
paper-marker list-routes
```

Run conversion:

```powershell
paper-marker convert path\to\paper.pdf --out-dir .\out --synthesize --openrouter-model openrouter/auto
```

Disable candidate bundle output:

```powershell
paper-marker convert path\to\paper.pdf --no-candidate-bundle
```

Keep intermediate route artifacts in `_work`:

```powershell
paper-marker convert path\to\paper.pdf --keep-temp
```

## Configuration

Copy `.env.example` to `.env` and set values as needed. All settings can also be exported as environment variables.

| Variable | Purpose | Default |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | OpenRouter API key for synthesis | — |
| `OPENAI_API_KEY` | Alternative API key (used if OpenRouter key unset) | — |
| `OPENAI_BASE_URL` | OpenAI-compatible API base URL | `https://openrouter.ai/api/v1` |
| `PAPER_MARKER_OPENROUTER_MODEL` | Default synthesis model | `openrouter/auto` |
| `PAPER_MARKER_TIMEOUT_PER_ROUTE` | Per-route subprocess timeout (seconds) | `300` |
| `PAPER_MARKER_MAX_PARALLEL_ROUTES` | Max parallel route workers | `4` |
| `PAPER_MARKER_SYNTH_MAX_CHARS_PER_CANDIDATE` | Synthesis prompt cap per candidate | `12000` |
| `PAPER_MARKER_SYNTH_MAX_TOTAL_CHARS` | Synthesis prompt cap total | `30000` |
| `PAPER_MARKER_SYNTH_HTTP_MAX_RETRIES` | Retries for transient synthesis HTTP errors | `2` |
| `PAPER_MARKER_SYNTH_HTTP_BACKOFF_SECONDS` | Base backoff between synthesis retries (seconds) | `1.0` |

For integration tests with real PDFs, also set `PAPER_MARKER_FIXTURE_CATALOG` (see `tests/fixtures/README.md`).

See `CONTRIBUTING.md` for development setup and `CHANGELOG.md` for release history.

## MCP Server (stdio)

```powershell
paper-marker-mcp
```

Tools:
- `convert_pdf_to_markdown`
- `list_conversion_routes`
- `validate_environment`

The `convert_pdf_to_markdown` tool also supports `keep_temp` for parity with the CLI.

## MCP Testing

See `docs/mcp_testing.md` for smoke checks, MCP contract tests, agent-style behavior tests, and CI tiering.

## CI/CD and Releases

- CI runs on pull requests and pushes to `main` in `.github/workflows/ci.yml`.
- PyPI publishing runs on tags like `vX.Y.Z` in `.github/workflows/publish.yml`.
- Tag versions must match `pyproject.toml` and must not already exist on PyPI.

Release flow:

```powershell
# 1) update version in pyproject.toml
git tag vX.Y.Z
git push origin vX.Y.Z
```

See `docs/release.md` for required GitHub/PyPI trusted publishing setup, rollback guidance, and deployment/install verification steps.

## Development Status

- Added issue ledger at `docs/implementation_issues.md`.
- Hardened route validation and contract parity (`--keep-temp` in CLI/MCP).
- Added synthesis prompt budget controls with provenance metadata.
- Added real fixture-matrix integration harness and fixture catalog template.
- Documented dataclass/Pydantic model boundary in `docs/modeling_policy.md`.
- Added curated web-sourced fixture catalog at `tests/fixtures/fixture_catalog.curated.json` and downloader utility `scripts/fetch_fixtures.py`.
- Added fixture catalog URL validator utility `scripts/validate_fixture_catalog.py`.
