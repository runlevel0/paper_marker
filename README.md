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
