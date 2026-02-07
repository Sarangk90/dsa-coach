"""Integration tests for MCP Obsidian client.

These tests require:
- OBSIDIAN_API_KEY set in .env
- Obsidian running with Local REST API plugin
- mcp-obsidian installable via uvx

Run with: pytest tests/mcp_client/test_integration.py -m integration
"""

from __future__ import annotations

import uuid

import pytest
from dotenv import load_dotenv

from dsa_coach.mcp.client import MCP_TOOL_PREFIX, MCPObsidianClient

load_dotenv()

# Skip all tests if no API key
pytestmark = pytest.mark.integration


@pytest.fixture
async def mcp_client():
    """Create and connect an MCP client, clean up after."""
    client = MCPObsidianClient()
    connected = await client.connect()
    if not connected:
        pytest.skip("MCP Obsidian not available (no API key or server)")
    yield client
    await client.close()


class TestMCPObsidianIntegration:
    """Integration tests that hit the real Obsidian vault."""

    async def test_connect_and_discover_tools(self, mcp_client: MCPObsidianClient):
        """Verify connection succeeds and tools are discovered."""
        tools = mcp_client.get_tools_for_llm()
        assert len(tools) > 0

        # Verify key tools are present
        tool_names = {t["name"] for t in tools}
        assert f"{MCP_TOOL_PREFIX}obsidian_append_content" in tool_names
        assert f"{MCP_TOOL_PREFIX}obsidian_get_file_contents" in tool_names
        assert f"{MCP_TOOL_PREFIX}obsidian_simple_search" in tool_names

    async def test_create_read_delete_note(self, mcp_client: MCPObsidianClient):
        """Create a test note, read it back, then delete it."""
        test_id = uuid.uuid4().hex[:8]
        test_path = f"_test/mcp-integration-{test_id}.md"
        test_content = f"# MCP Integration Test\n\nTest ID: {test_id}\n"

        # Create note
        create_result = await mcp_client.call_tool(
            f"{MCP_TOOL_PREFIX}obsidian_append_content",
            {"filepath": test_path, "content": test_content},
        )
        assert "Error" not in create_result, f"Create failed: {create_result}"

        # Read it back
        read_result = await mcp_client.call_tool(
            f"{MCP_TOOL_PREFIX}obsidian_get_file_contents",
            {"filepath": test_path},
        )
        assert test_id in read_result, f"Read didn't contain test ID: {read_result}"

        # Clean up — delete the test file
        delete_result = await mcp_client.call_tool(
            f"{MCP_TOOL_PREFIX}obsidian_delete_file",
            {"filepath": test_path},
        )
        assert "Error" not in delete_result, f"Delete failed: {delete_result}"

    async def test_search_vault(self, mcp_client: MCPObsidianClient):
        """Verify vault search works."""
        result = await mcp_client.call_tool(
            f"{MCP_TOOL_PREFIX}obsidian_simple_search",
            {"query": "sliding window", "context_length": 50},
        )
        # Search may return empty but shouldn't error
        assert isinstance(result, str)

    async def test_tools_have_correct_schema(self, mcp_client: MCPObsidianClient):
        """Verify tool schemas are in Anthropic format."""
        tools = mcp_client.get_tools_for_llm()
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert tool["name"].startswith(MCP_TOOL_PREFIX)
            assert isinstance(tool["input_schema"], dict)

    async def test_is_mcp_tool_distinguishes_correctly(
        self, mcp_client: MCPObsidianClient
    ):
        """Verify is_mcp_tool works with real tool names."""
        tools = mcp_client.get_tools_for_llm()
        for tool in tools:
            assert mcp_client.is_mcp_tool(tool["name"]) is True

        # Local tools should not match
        assert mcp_client.is_mcp_tool("get_dashboard") is False
        assert mcp_client.is_mcp_tool("start_quest") is False
