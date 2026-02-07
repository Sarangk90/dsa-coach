"""MCP client for mcp-obsidian server.

Spawns mcp-obsidian as a subprocess via uvx, discovers tools,
converts schemas to Anthropic format, and routes tool calls.
Gracefully degrades when Obsidian/API key is unavailable.
"""

from __future__ import annotations

import contextlib
import logging
import os
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

# Prefix to distinguish MCP tools from local registry tools
MCP_TOOL_PREFIX = "mcp_obsidian__"


class MCPObsidianClient:
    """Client for the mcp-obsidian MCP server."""

    def __init__(self) -> None:
        self._session: ClientSession | None = None
        self._tools: list[dict] = []
        self._tool_names: set[str] = set()
        self._cm: Any = None  # context manager for stdio_client
        self._read: Any = None
        self._write: Any = None
        self._session_cm: Any = None

    async def connect(self) -> bool:
        """Connect to the mcp-obsidian server.

        Returns:
            True if connected successfully, False otherwise.
        """
        api_key = os.getenv("OBSIDIAN_API_KEY", "").strip()
        if not api_key:
            logger.debug("OBSIDIAN_API_KEY not set, MCP notes disabled")
            return False

        command = os.getenv("OBSIDIAN_MCP_COMMAND", "uvx").strip()

        server_params = StdioServerParameters(
            command=command,
            args=["mcp-obsidian"],
            env={**os.environ, "OBSIDIAN_API_KEY": api_key},
        )

        try:
            self._cm = stdio_client(server_params)
            self._read, self._write = await self._cm.__aenter__()

            self._session_cm = ClientSession(self._read, self._write)
            self._session = await self._session_cm.__aenter__()

            await self._session.initialize()

            # Discover tools
            result = await self._session.list_tools()
            self._tools = [self._to_anthropic_format(t) for t in result.tools]
            self._tool_names = {t["name"] for t in self._tools}

            logger.info(
                "MCP Obsidian connected: %d tools available",
                len(self._tools),
            )
            return True

        except Exception:
            logger.debug("MCP Obsidian connection failed", exc_info=True)
            await self.close()
            return False

    def get_tools_for_llm(self) -> list[dict]:
        """Get MCP tools in Anthropic tool format."""
        return list(self._tools)

    def is_mcp_tool(self, tool_name: str) -> bool:
        """Check if a tool name belongs to MCP."""
        return tool_name in self._tool_names

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Execute an MCP tool call.

        Returns:
            Tool result as a string.
        """
        if not self._session:
            return "Error: MCP session not connected"

        # Strip prefix for the actual MCP call
        mcp_name = tool_name
        if mcp_name.startswith(MCP_TOOL_PREFIX):
            mcp_name = mcp_name[len(MCP_TOOL_PREFIX) :]

        result = await self._session.call_tool(mcp_name, arguments)

        # Extract text from result content blocks
        parts = []
        for block in result.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts) if parts else "OK"

    async def close(self) -> None:
        """Clean up MCP session and subprocess."""
        if self._session_cm:
            with contextlib.suppress(Exception):
                await self._session_cm.__aexit__(None, None, None)
            self._session_cm = None
            self._session = None

        if self._cm:
            with contextlib.suppress(Exception):
                await self._cm.__aexit__(None, None, None)
            self._cm = None

        self._tools = []
        self._tool_names = set()

    @staticmethod
    def _to_anthropic_format(mcp_tool: Any) -> dict:
        """Convert an MCP tool schema to Anthropic tool format."""
        return {
            "name": f"{MCP_TOOL_PREFIX}{mcp_tool.name}",
            "description": mcp_tool.description or "",
            "input_schema": (
                mcp_tool.inputSchema
                if mcp_tool.inputSchema
                else {"type": "object", "properties": {}}
            ),
        }
