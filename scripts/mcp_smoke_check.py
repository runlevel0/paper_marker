from __future__ import annotations

from pathlib import Path
import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

EXPECTED_TOOLS = {"list_conversion_routes", "validate_environment", "convert_pdf_to_markdown"}


async def _run_smoke() -> None:
    root = Path(__file__).resolve().parents[1]
    params = StdioServerParameters(
        command="uv",
        args=["run", "--no-sync", "paper-marker-mcp"],
        cwd=root,
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            tool_defs = [tool.model_dump(mode="json") for tool in tools.tools]
            names = {tool.get("name") for tool in tool_defs}
            missing = EXPECTED_TOOLS - names
            if missing:
                raise RuntimeError(f"Missing expected MCP tools: {sorted(missing)}")
            for tool in tool_defs:
                if not isinstance(tool.get("inputSchema"), dict):
                    raise RuntimeError(f"Tool schema missing or invalid for {tool.get('name')}")
            print(f"MCP smoke check passed: discovered {len(tool_defs)} tools.")


if __name__ == "__main__":
    anyio.run(_run_smoke)

