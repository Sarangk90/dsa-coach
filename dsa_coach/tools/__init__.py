"""Tools module for DSA Coach agent.

This module contains all tools available to the CoachAgent
for managing patterns, quests, progress, code, and more.
"""

from .registry import ToolRegistry, ToolResult, tool

# Import all tools to register them
from . import patterns
from . import quests
from . import progress
from . import code
from . import teaching
from . import external
from . import obsidian

__all__ = [
    "ToolRegistry",
    "ToolResult", 
    "tool",
    "patterns",
    "quests",
    "progress",
    "code",
    "teaching",
    "external",
    "obsidian",
]

