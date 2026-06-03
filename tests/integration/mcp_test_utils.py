from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import TextContent


@dataclass
class McpServerProcess:
    command: list[str]
    cwd: Path
    env: dict[str, str] | None = None

    async def _run_with_session(self, callback: Any) -> Any:
        stack = contextlib.AsyncExitStack()
        try:
            params = StdioServerParameters(
                command=self.command[0],
                args=self.command[1:],
                cwd=self.cwd,
                env=self.env,
            )
            read_stream, write_stream = await stack.enter_async_context(stdio_client(params))
            session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
            await session.initialize()
            return await callback(session)
        finally:
            await stack.aclose()

    async def _list_tools_async(self) -> list[dict[str, Any]]:
        async def _list(session: ClientSession) -> list[dict[str, Any]]:
            result = await session.list_tools()
            return [tool.model_dump(mode="json") for tool in result.tools]

        return await self._run_with_session(_list)

    async def _call_tool_async(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        async def _call(session: ClientSession) -> Any:
            result = await session.call_tool(name, arguments or {})
            return decode_tool_result(result)

        return await self._run_with_session(_call)

    def list_tools(self) -> list[dict[str, Any]]:
        return anyio.run(self._list_tools_async)

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        return anyio.run(self._call_tool_async, name, arguments)


def decode_tool_result(result: Any) -> Any:
    content = getattr(result, "content", None)
    if not isinstance(content, list):
        return result
    if len(content) == 1 and isinstance(content[0], TextContent):
        text = content[0].text
        if text.startswith("{") or text.startswith("["):
            try:
                return json.loads(text)
            except ValueError:
                return text
        return text
    decoded: list[Any] = []
    for item in content:
        if isinstance(item, TextContent):
            text = item.text
            if text.startswith("{") or text.startswith("["):
                try:
                    decoded.append(json.loads(text))
                    continue
                except ValueError:
                    pass
            decoded.append(text)
            continue
        decoded.append(item.model_dump(mode="json") if hasattr(item, "model_dump") else item)
    return decoded
