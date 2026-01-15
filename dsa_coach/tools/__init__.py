"""Tools module for DSA Coach agent.

This module contains all tools available to the CoachAgent
for managing patterns, quests, progress, code, and more.

Tool Architecture:
- Legacy tools (deprecated): In individual modules (patterns, quests, progress, etc.)
- Consolidated tools (15): In consolidated.py for workflow-level operations

The SDK agent uses only consolidated tools by default.
Legacy tools are marked as deprecated and will emit warnings when used.
"""

# Import all tools to register them
# NOTE: consolidated is imported LAST so its tools take precedence over legacy
from . import (
    code,
    consolidated,  # LAST: 15 workflow-level tools override legacy
    external,
    obsidian,
    patterns,
    progress,
    quests,
    teaching,
)
from .registry import ToolRegistry, ToolResult, tool

# Mark legacy tools as deprecated
_registry = ToolRegistry()
_deprecated_count = _registry.mark_all_deprecated_from_map()

__all__ = [
    "ToolRegistry",
    "ToolResult",
    "tool",
    # Legacy tool modules (deprecated)
    "patterns",
    "quests",
    "progress",
    "code",
    "teaching",
    "external",
    "obsidian",
    # Consolidated tools module (recommended)
    "consolidated",
]
