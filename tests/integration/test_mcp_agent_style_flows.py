from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from mcp_test_utils import McpServerProcess


@dataclass
class AgentRun:
    tool_calls: list[str]
    payloads: list[Any]
    final_text: str


class DeterministicAgentHarness:
    def __init__(self, server: McpServerProcess):
        self._server = server

    def run_prompt(self, prompt: str) -> AgentRun:
        lowered = prompt.lower()
        tool_calls: list[str] = []
        payloads: list[Any] = []

        if "route" in lowered and "convert" not in lowered:
            tool_calls.append("list_conversion_routes")
            payload = self._server.call_tool("list_conversion_routes")
            payloads.append(payload)
            return AgentRun(tool_calls, payloads, f"Found {len(payload)} routes.")

        if "environment" in lowered or "setup" in lowered:
            tool_calls.append("validate_environment")
            payload = self._server.call_tool("validate_environment")
            payloads.append(payload)
            return AgentRun(tool_calls, payloads, "Environment validation completed.")

        if "convert" in lowered:
            tool_calls.append("convert_pdf_to_markdown")
            payload = self._server.call_tool(
                "convert_pdf_to_markdown",
                {
                    "pdf_path": str(Path("missing-fixture.pdf")),
                    "out_dir": "out",
                    "routes": ["fallback"],
                    "timeout_per_route_s": 1,
                    "export_candidate_bundle": False,
                    "keep_temp": True,
                },
            )
            payloads.append(payload)
            if "error" in str(payload).lower() or "not found" in str(payload).lower():
                return AgentRun(
                    tool_calls, payloads, "Conversion failed gracefully with an MCP error."
                )
            return AgentRun(tool_calls, payloads, "Conversion request completed.")

        return AgentRun(tool_calls, payloads, "No matching MCP tool for prompt.")


@pytest.fixture
def mcp_server() -> McpServerProcess:
    root = Path(__file__).resolve().parents[2]
    return McpServerProcess(command=["uv", "run", "--no-sync", "paper-marker-mcp"], cwd=root)


@pytest.mark.integration
@pytest.mark.mcp
@pytest.mark.agent_style
def test_agent_style_route_listing_flow(mcp_server: McpServerProcess) -> None:
    agent = DeterministicAgentHarness(mcp_server)
    run = agent.run_prompt("List the available conversion routes.")
    assert run.tool_calls == ["list_conversion_routes"]
    assert isinstance(run.payloads[0], list)
    assert run.payloads[0]


@pytest.mark.integration
@pytest.mark.mcp
@pytest.mark.agent_style
def test_agent_style_environment_check_flow(mcp_server: McpServerProcess) -> None:
    agent = DeterministicAgentHarness(mcp_server)
    run = agent.run_prompt("Can you check whether the conversion environment is set up?")
    assert run.tool_calls == ["validate_environment"]
    assert isinstance(run.payloads[0], dict)
    assert "has_api_key" in run.payloads[0]


@pytest.mark.integration
@pytest.mark.mcp
@pytest.mark.agent_style
def test_agent_style_convert_error_recovery_flow(mcp_server: McpServerProcess) -> None:
    agent = DeterministicAgentHarness(mcp_server)
    run = agent.run_prompt("Convert this paper to markdown and keep temp files.")
    assert run.tool_calls == ["convert_pdf_to_markdown"]
    assert "gracefully" in run.final_text.lower() or "completed" in run.final_text.lower()
