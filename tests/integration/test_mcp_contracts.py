from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from mcp_test_utils import McpServerProcess


@pytest.fixture
def mcp_server() -> McpServerProcess:
    root = Path(__file__).resolve().parents[2]
    return McpServerProcess(command=["uv", "run", "--no-sync", "paper-marker-mcp"], cwd=root)


@pytest.mark.integration
@pytest.mark.mcp
def test_mcp_tools_list_contract(mcp_server: McpServerProcess) -> None:
    tools = mcp_server.list_tools()
    names = {tool["name"] for tool in tools}
    assert {
        "list_conversion_routes",
        "validate_environment",
        "convert_pdf_to_markdown",
    }.issubset(names)
    for tool in tools:
        assert isinstance(tool.get("description"), str)
        assert isinstance(tool.get("inputSchema"), dict)


@pytest.mark.integration
@pytest.mark.mcp
def test_validate_environment_contract(mcp_server: McpServerProcess) -> None:
    payload = mcp_server.call_tool("validate_environment")
    assert isinstance(payload, dict)
    assert "routes" in payload
    assert "openai_base_url" in payload
    assert "has_api_key" in payload
    assert isinstance(payload["routes"], list)
    assert isinstance(payload["has_api_key"], bool)


@pytest.mark.integration
@pytest.mark.mcp
def test_list_conversion_routes_contract(mcp_server: McpServerProcess) -> None:
    routes = mcp_server.call_tool("list_conversion_routes")
    assert isinstance(routes, list)
    assert routes
    first = routes[0]
    assert isinstance(first, dict)
    assert "route" in first
    assert "available" in first


@pytest.mark.integration
@pytest.mark.mcp
def test_convert_pdf_to_markdown_input_validation_error(mcp_server: McpServerProcess) -> None:
    bad_path = str(Path("nonexistent") / "missing.pdf")
    payload = mcp_server.call_tool(
        "convert_pdf_to_markdown",
        {
            "pdf_path": bad_path,
            "out_dir": "out",
            "routes": ["fallback"],
            "timeout_per_route_s": 1,
            "export_candidate_bundle": False,
        },
    )
    assert isinstance(payload, list | str | dict)
    text = _payload_to_text(payload)
    assert "error" in text.lower() or "not found" in text.lower()


def _payload_to_text(payload: Any) -> str:
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        return str(payload)
    return " ".join(str(item) for item in payload)

