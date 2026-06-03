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

Commands:

| Command | Purpose |
| --- | --- |
| `list-routes` | JSON list of route names and whether each converter CLI is on `PATH` |
| `doctor` | Route availability plus synthesis API base URL and whether a key is configured |
| `convert` | Run parallel conversion and write outputs under `--out-dir` |

List available routes:

```powershell
paper-marker list-routes
```

Check environment (routes + synthesis credentials):

```powershell
paper-marker doctor
```

Run conversion (all default routes):

```powershell
paper-marker convert path\to\paper.pdf --out-dir .\out
```

Run a subset of routes with a custom per-route timeout:

```powershell
paper-marker convert path\to\paper.pdf --out-dir .\out --routes marker --routes markitdown --timeout-per-route 600
```

Valid route names: `marker`, `mineru`, `nougat`, `markitdown` (repeat `--routes` to select more than one).

Enable LLM synthesis (requires `OPENROUTER_API_KEY` or `OPENAI_API_KEY`):

```powershell
paper-marker convert path\to\paper.pdf --out-dir .\out --synthesize --openrouter-model openrouter/auto
```

Disable candidate bundle output:

```powershell
paper-marker convert path\to\paper.pdf --out-dir .\out --no-candidate-bundle
```

Keep intermediate route artifacts in `_work`:

```powershell
paper-marker convert path\to\paper.pdf --out-dir .\out --keep-temp
```

### Convert outputs

Under `--out-dir` the pipeline writes:

| Artifact | Description |
| --- | --- |
| `final.md` | Selected or synthesized Markdown (when any route succeeds) |
| `final_result.json` | Full run payload (candidates, selection, synthesis metadata) |
| `run_report.json` | Timing and selection summary |
| `candidate_bundle/` | Per-route Markdown and metadata (unless `--no-candidate-bundle`) |
| `_work/` | Intermediate route workspaces (only with `--keep-temp`) |

`convert` prints the same `final_result` JSON to stdout.

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

Start the server (stdio transport):

```powershell
uv run paper-marker-mcp
```

Or after `uv tool install`, use `paper-marker-mcp` on your `PATH`.

### Tools

| Tool | CLI equivalent | Purpose |
| --- | --- | --- |
| `list_conversion_routes` | `list-routes` | Route names and availability |
| `validate_environment` | `doctor` | Routes, API base URL, `has_api_key` |
| `convert_pdf_to_markdown` | `convert` | Run conversion; same outputs under `out_dir` |

### `convert_pdf_to_markdown` parameters

| Parameter | Required | Default | Notes |
| --- | --- | --- | --- |
| `pdf_path` | yes | — | Input PDF path |
| `out_dir` | yes | — | Output directory (no implicit default) |
| `routes` | no | all four routes | e.g. `["marker", "markitdown"]` |
| `timeout_per_route_s` | no | `300` | Per-route timeout in seconds |
| `synthesize` | no | `false` | LLM merge when API key is set |
| `openrouter_model` | no | env default | Model override for synthesis |
| `export_candidate_bundle` | no | `true` | Set `false` to skip `candidate_bundle/` |
| `keep_temp` | no | `false` | Keep `_work/` after the run |

### Sample client configuration

**Cursor** (`.cursor/mcp.json` in the project or user config):

```json
{
  "mcpServers": {
    "paper-marker": {
      "command": "uv",
      "args": ["run", "--directory", "C:\\path\\to\\paper_marker", "paper-marker-mcp"]
    }
  }
}
```

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "paper-marker": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/paper_marker", "paper-marker-mcp"]
    }
  }
}
```

Replace the `--directory` path with your clone. For a global `uv tool install`, you can use `"command": "paper-marker-mcp"` with an empty `args` array when the tool is on `PATH`.

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

- Track work in [GitHub Issues](https://github.com/runlevel0/paper_marker/issues) (migrated from the former markdown ledger; archives under `docs/archive/`).
- Hardened route validation and contract parity (`--keep-temp` in CLI/MCP).
- Added synthesis prompt budget controls with provenance metadata.
- Added real fixture-matrix integration harness and fixture catalog template.
- Documented dataclass/Pydantic model boundary in `docs/modeling_policy.md`.
- Added curated web-sourced fixture catalog at `tests/fixtures/fixture_catalog.curated.json` and downloader utility `scripts/fetch_fixtures.py`.
- Added fixture catalog URL validator utility `scripts/validate_fixture_catalog.py`.
