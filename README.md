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

For synthesis with OpenRouter/OpenAI-compatible APIs:
- `OPENROUTER_API_KEY` or `OPENAI_API_KEY`
- `OPENAI_BASE_URL` (default `https://openrouter.ai/api/v1`)
- `PAPER_MARKER_OPENROUTER_MODEL` (default model name)

## MCP Server (stdio)

```powershell
paper-marker-mcp
```

Tools:
- `convert_pdf_to_markdown`
- `list_conversion_routes`
- `validate_environment`

The `convert_pdf_to_markdown` tool also supports `keep_temp` for parity with the CLI.

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
