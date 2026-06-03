# Installation

`paper-marker` is distributed on [PyPI](https://pypi.org/project/paper-marker/) as the package
`paper-marker`. It exposes two console scripts:

| Command | Purpose |
| --- | --- |
| `paper-marker` | Typer CLI (`list-routes`, `doctor`, `convert`) |
| `paper-marker-mcp` | stdio MCP server |

Converter routes invoke external CLIs (`marker`, `magic-pdf`, `nougat`, `markitdown`). Those
tools are **not** bundled in the base wheel; install optional extras or provide the CLIs on
`PATH` yourself (see [Route extras](#route-extras)).

## Requirements

- Python 3.11 or newer
- Recommended: [uv](https://docs.astral.sh/uv/) for tool installs and virtual environments

## Install from PyPI

### CLI and MCP (recommended)

Install into an isolated tool environment with uv:

```powershell
uv tool install paper-marker
```

Pin a release for reproducibility:

```powershell
uv tool install "paper-marker==0.1.0"
```

After install, both entry points should be on your `PATH` (uv manages the tool environment).

### pip / venv

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install paper-marker
```

On Linux/macOS, activate with `source .venv/bin/activate` instead.

## Verify the install

Run these commands in a **new** shell after `uv tool install` so `PATH` picks up the tool
environment.

```powershell
paper-marker --help
paper-marker list-routes
paper-marker doctor
```

MCP stdio server (should start and wait on stdin; stop with Ctrl+C):

```powershell
paper-marker-mcp --help
```

Automated smoke (builds a wheel, installs into a temporary venv, checks CLI + MCP `tools/list`):

```powershell
uv run python scripts/install_smoke_check.py
```

From a repository checkout you can also run the pytest wrapper (not part of default CI unit
selection):

```powershell
uv run pytest tests/unit/test_install_smoke.py -m install_smoke
```

## Route extras

Heavy converter dependencies are optional. With uv tool install:

```powershell
uv tool install "paper-marker[all]"
```

With pip:

```powershell
python -m pip install "paper-marker[all]"
```

Individual extras: `marker`, `mineru`, `nougat`, `fallback` (MarkItDown). See `pyproject.toml`
for exact optional dependency names.

Route CLIs installed as dependencies of a uv tool environment are discovered automatically; you
do not need to add the tool `Scripts` directory to `PATH` manually.

## LLM synthesis

Synthesis uses an OpenAI-compatible API (OpenRouter by default). Set one of:

- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY`

Copy `.env.example` to `.env` or export variables in your shell. See the README configuration
table for all `PAPER_MARKER_*` settings.

## MCP client configuration

After a global install, point your MCP client at the installed script:

```json
{
  "mcpServers": {
    "paper-marker": {
      "command": "paper-marker-mcp",
      "args": []
    }
  }
}
```

For development from a clone, use `uv run paper-marker-mcp` or
`uv run --directory C:\\path\\to\\paper_marker paper-marker-mcp` — see `docs/mcp_testing.md`.

## Development install

Contributors use an editable workspace install, not the PyPI wheel:

```powershell
uv sync --extra llm
uv run paper-marker list-routes
```

See `CONTRIBUTING.md` for lint, test, and issue workflow commands.

## Troubleshooting

| Symptom | Likely cause | What to try |
| --- | --- | --- |
| `paper-marker` not found | Tool env not on `PATH` | Open a new shell; run `uv tool list` and reinstall |
| All routes `available: false` | Converter CLIs missing | Install `[all]` extra or install route CLIs manually |
| MCP client cannot start server | Wrong `command` / cwd | Use `paper-marker-mcp` after tool install; for clones use `uv run` |
| Synthesis skipped | No API key | Set `OPENROUTER_API_KEY` or `OPENAI_API_KEY`; run `paper-marker doctor` |
