"""Tools module for DSA Coach agent.

This module contains all tools available to the CoachAgent
for managing patterns, quests, progress, code, and more.
"""

# Import all tools to register them
from . import code, external, obsidian, patterns, progress, quests, teaching
from .registry import ToolRegistry, ToolResult, tool

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
