# MCP Testing

This project uses a layered MCP test strategy so we can catch protocol regressions early and still validate real agent-style usage.

## Local Commands

Run install/startup and protocol smoke checks:

```powershell
uv run python scripts/mcp_smoke_check.py
```

Validate PyPI-style install (wheel build, clean venv, installed `paper-marker-mcp` entry point):

```powershell
uv run python scripts/install_smoke_check.py
```

See [`installation.md`](installation.md) for end-user install commands.

Run MCP contract tests:

```powershell
uv run pytest -q tests/integration/test_mcp_contracts.py
```

Run agent-style MCP behavior tests:

```powershell
uv run pytest -q tests/integration/test_mcp_agent_style_flows.py
```

Run all MCP-marked integration tests:

```powershell
uv run pytest -q -m "integration and mcp"
```

## Optional Inspector Checks

Use MCP Inspector for an interactive or scriptable protocol-level validation pass:

```powershell
npx -y @modelcontextprotocol/inspector --cli uv run paper-marker-mcp --method tools/list
```

This is useful for debugging schema/capability issues when adding new tools.

## CI Tiers

- Tier A (required on pull requests): smoke + MCP contracts.
- Tier B (nightly): agent-style behavior tests.

Tier A should stay fast and deterministic. Tier B can cover richer end-to-end flows.

