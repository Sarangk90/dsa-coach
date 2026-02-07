"""Tests for MCPObsidianClient."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from dsa_coach.mcp.client import MCP_TOOL_PREFIX, MCPObsidianClient


class TestMCPObsidianClient:
    """Unit tests for MCPObsidianClient."""

    def test_initial_state(self):
        client = MCPObsidianClient()
        assert client.get_tools_for_llm() == []
        assert client.is_mcp_tool("anything") is False

    @patch.dict("os.environ", {"OBSIDIAN_API_KEY": ""}, clear=False)
    async def test_connect_returns_false_without_api_key(self):
        client = MCPObsidianClient()
        result = await client.connect()
        assert result is False
        assert client.get_tools_for_llm() == []

    @patch.dict("os.environ", {"OBSIDIAN_API_KEY": "test-key"}, clear=False)
    @patch("dsa_coach.mcp.client.stdio_client")
    async def test_connect_returns_false_on_server_failure(self, mock_stdio_client):
        # Simulate server spawn failure
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(side_effect=OSError("spawn failed"))
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        mock_stdio_client.return_value = mock_cm

        client = MCPObsidianClient()
        result = await client.connect()
        assert result is False

    def test_to_anthropic_format(self):
        mock_tool = MagicMock()
        mock_tool.name = "get_file_contents"
        mock_tool.description = "Read a file from the vault"
        mock_tool.inputSchema = {
            "type": "object",
            "properties": {"filepath": {"type": "string"}},
            "required": ["filepath"],
        }

        result = MCPObsidianClient._to_anthropic_format(mock_tool)

        assert result["name"] == f"{MCP_TOOL_PREFIX}get_file_contents"
        assert result["description"] == "Read a file from the vault"
        assert result["input_schema"]["properties"]["filepath"]["type"] == "string"

    def test_is_mcp_tool_after_tools_loaded(self):
        client = MCPObsidianClient()
        # Simulate loaded tools
        client._tool_names = {
            f"{MCP_TOOL_PREFIX}get_file_contents",
            f"{MCP_TOOL_PREFIX}search",
        }
        assert client.is_mcp_tool(f"{MCP_TOOL_PREFIX}get_file_contents") is True
        assert client.is_mcp_tool(f"{MCP_TOOL_PREFIX}search") is True
        assert client.is_mcp_tool("get_dashboard") is False

    def test_get_tools_for_llm_returns_copies(self):
        client = MCPObsidianClient()
        client._tools = [{"name": "test", "description": "", "input_schema": {}}]
        tools = client.get_tools_for_llm()
        assert len(tools) == 1
        assert tools is not client._tools

    async def test_call_tool_without_session(self):
        client = MCPObsidianClient()
        result = await client.call_tool("test_tool", {})
        assert "not connected" in result

    async def test_call_tool_strips_prefix(self):
        client = MCPObsidianClient()
        mock_session = AsyncMock()

        # Mock result with text content block
        mock_block = MagicMock()
        mock_block.text = "file contents here"
        mock_result = MagicMock()
        mock_result.content = [mock_block]
        mock_session.call_tool = AsyncMock(return_value=mock_result)

        client._session = mock_session

        result = await client.call_tool(
            f"{MCP_TOOL_PREFIX}get_file_contents",
            {"filepath": "test.md"},
        )

        # Should strip the prefix when calling MCP
        mock_session.call_tool.assert_called_once_with(
            "get_file_contents", {"filepath": "test.md"}
        )
        assert result == "file contents here"

    async def test_close_cleans_up(self):
        client = MCPObsidianClient()
        client._tools = [{"name": "test"}]
        client._tool_names = {"test"}
        client._session = MagicMock()
        client._session_cm = None
        client._cm = None

        await client.close()

        assert client._tools == []
        assert client._tool_names == set()
