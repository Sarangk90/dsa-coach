"""Tools module for DSA Coach agent.

Only consolidated workflow-level tools are supported.
"""

# Import consolidated tools to register all supported tool definitions.
from . import consolidated, pattern_learning, progress_review, session_quest
from .registry import ToolRegistry, ToolResult, tool

__all__ = [
    "ToolRegistry",
    "ToolResult",
    "tool",
    "consolidated",
    "session_quest",
    "pattern_learning",
    "progress_review",
]
