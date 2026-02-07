"""MCP (Model Context Protocol) integration for Obsidian notes.

Connects to mcp-obsidian server via the MCP Python SDK,
exposing Obsidian vault tools to the coaching agent.
"""

from .client import MCPObsidianClient

__all__ = ["MCPObsidianClient"]
