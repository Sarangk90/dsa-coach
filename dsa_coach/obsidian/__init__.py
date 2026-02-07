"""Obsidian integration — analyzer only.

Note creation and vault I/O are handled by the mcp-obsidian MCP server.
This module retains the analyzer for determining when notes should be created.
"""

from .analyzer import should_create_note

__all__ = ["should_create_note"]
