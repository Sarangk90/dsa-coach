"""Tool registry for DSA Coach agent.

Provides a decorator-based registry system for agent tools
and utilities for converting to LLM-compatible tool schemas.
"""

import inspect
import warnings
from collections.abc import Callable
from functools import wraps
from typing import Any, get_type_hints

from pydantic import BaseModel, Field

# Global registry of all tools
_TOOL_REGISTRY: dict[str, "RegisteredTool"] = {}


class ToolResult(BaseModel):
    """Standard result from a tool execution."""

    success: bool = True
    data: Any = None
    message: str | None = None
    error: str | None = None


class RegisteredTool(BaseModel):
    """Metadata about a registered tool."""

    model_config = {"arbitrary_types_allowed": True}

    name: str
    description: str
    category: str
    func: Callable = Field(exclude=True)
    parameters_schema: dict = Field(default_factory=dict)
    is_deprecated: bool = False
    deprecation_message: str | None = None
    replacement: str | None = None


def tool(
    name: str | None = None,
    description: str | None = None,
    category: str = "general",
) -> Callable:
    """
    Decorator to register a function as an agent tool.

    Usage:
        @tool(name="list_patterns", description="List all available patterns", category="patterns")
        async def list_patterns() -> ToolResult:
            ...
    """

    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Tool: {tool_name}"

        # Build parameter schema from type hints
        hints = get_type_hints(func) if hasattr(func, "__annotations__") else {}
        sig = inspect.signature(func)

        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "db", "ctx"):  # Skip context params
                continue

            param_type = hints.get(param_name, str)

            # Map Python types to JSON schema types
            json_type = "string"
            if param_type is int:
                json_type = "integer"
            elif param_type is float:
                json_type = "number"
            elif param_type is bool:
                json_type = "boolean"
            elif param_type is list:
                json_type = "array"
            elif param_type is dict:
                json_type = "object"

            prop = {"type": json_type}

            # Add description from docstring if available
            if func.__doc__:
                # Try to extract parameter description from docstring
                doc_lines = func.__doc__.split("\n")
                for line in doc_lines:
                    if f":param {param_name}:" in line or "Args:" in line:
                        # Simple extraction, could be improved
                        pass

            properties[param_name] = prop

            # Check if parameter is required (no default value)
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        parameters_schema = {
            "type": "object",
            "properties": properties,
            "required": required,
        }

        # Register the tool
        registered = RegisteredTool(
            name=tool_name,
            description=tool_description.strip(),
            category=category,
            func=func,
            parameters_schema=parameters_schema,
        )
        _TOOL_REGISTRY[tool_name] = registered

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        wrapper._tool_info = registered  # type: ignore[attr-defined]
        return wrapper

    return decorator


def deprecated_tool(
    replacement: str | None = None,
    message: str | None = None,
) -> Callable:
    """
    Decorator to mark a tool as deprecated.

    This should be applied AFTER the @tool decorator.

    Usage:
        @deprecated_tool(replacement="start_quest", message="Use start_quest instead")
        @tool(name="assign_quest", ...)
        async def assign_quest(...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        # Get the registered tool info if available
        if hasattr(func, "_tool_info"):
            tool_info = func._tool_info
            tool_info.is_deprecated = True
            tool_info.replacement = replacement
            tool_info.deprecation_message = (
                message
                or f"'{tool_info.name}' is deprecated. Use '{replacement}' instead."
            )

            # Update in global registry
            _TOOL_REGISTRY[tool_info.name] = tool_info

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Emit deprecation warning when called
            if hasattr(func, "_tool_info"):
                tool_info = func._tool_info
                warnings.warn(
                    tool_info.deprecation_message
                    or f"Tool '{tool_info.name}' is deprecated",
                    DeprecationWarning,
                    stacklevel=2,
                )
            return await func(*args, **kwargs)

        # Preserve tool info on wrapper
        if hasattr(func, "_tool_info"):
            wrapper._tool_info = func._tool_info  # type: ignore[attr-defined]

        return wrapper

    return decorator


# Mapping of old tool names to their consolidated replacements
TOOL_DEPRECATION_MAP: dict[str, str] = {
    # quests.py tools
    "assign_quest": "start_quest",
    "mark_quest_complete": "complete_quest",
    "get_next_recommended_quest": "start_quest",
    "get_quests_for_pattern": "get_pattern_details",
    "get_current_quest": "get_dashboard",
    # patterns.py tools
    "get_weak_patterns": "list_patterns(sort_by='progress')",
    "get_next_essential_quest": "start_quest(pattern_id=...)",
    # progress.py tools
    "get_user_profile": "get_dashboard",
    "get_session_state": "get_dashboard",
    "get_learning_history": "get_progress_summary",
    "get_due_reviews": "get_progress_summary",
    # teaching.py tools
    "diagnose_pattern_understanding": "diagnose_understanding",
    "record_concept_understanding": "record_learning(type='concept_understood')",
    "get_concept_gaps": "diagnose_understanding",
    "mark_concept_taught": "record_learning(type='concept_taught')",
    "record_mistake": "record_learning(type='mistake')",
    "record_teaching": "record_learning(type='concept_taught')",
    "get_recent_mistakes": "get_teaching_context",
    "log_session_activity": "[automatic via complete_quest hook]",
    "add_milestone": "record_learning(type='milestone')",
    "get_teaching_history_for_pattern": "get_teaching_context",
    # code.py tools
    "create_solution_file": "manage_solution(action='create')",
    "read_solution_file": "manage_solution(action='read')",
    "list_solution_files": "manage_solution(action='list')",
    "get_solution_template": "manage_solution(action='template')",
    # external.py tools
    "open_browser": "[internal to start_quest]",
    "open_leetcode_problem": "[internal to start_quest]",
    "get_dashboard_state": "get_dashboard",
    "search_patterns_and_quests": "[removed - rarely used]",
    # obsidian.py tools
    "propose_pattern_note": "[internal to create_note]",
    "create_pattern_note": "create_note(type='pattern')",
    "list_existing_notes": "[internal to create_note]",
    "update_note_with_insights": "update_note",
    "check_note_creation_criteria": "[internal to create_note]",
    "create_problem_note": "create_note(type='problem')",
}


def get_deprecation_info(tool_name: str) -> tuple[bool, str | None]:
    """Get deprecation info for a tool.

    Returns:
        Tuple of (is_deprecated, replacement)
    """
    if tool_name in TOOL_DEPRECATION_MAP:
        return True, TOOL_DEPRECATION_MAP[tool_name]
    return False, None


class ToolRegistry:
    """Registry for managing and executing agent tools."""

    def __init__(self):
        self._tools = _TOOL_REGISTRY

    def get_tool(self, name: str) -> RegisteredTool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(
        self,
        category: str | None = None,
        include_deprecated: bool = True,
    ) -> list[RegisteredTool]:
        """List all registered tools, optionally filtered by category and deprecation.

        Args:
            category: Filter by category if provided
            include_deprecated: If False, exclude deprecated tools (default True)
        """
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        if not include_deprecated:
            tools = [t for t in tools if not t.is_deprecated]
        return tools

    def list_consolidated_tools(self) -> list[RegisteredTool]:
        """List only the 15 consolidated workflow-level tools."""
        return self.list_tools(category="consolidated")

    def list_categories(self) -> list[str]:
        """Get all unique tool categories."""
        return list({t.category for t in self._tools.values()})

    async def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name with given arguments."""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found",
            )

        try:
            # Filter kwargs to only include parameters the function accepts
            sig = inspect.signature(tool.func)
            valid_params = set(sig.parameters.keys())
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}

            result = await tool.func(**filtered_kwargs)
            if isinstance(result, ToolResult):
                return result
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}",
            )

    def to_anthropic_tools(
        self,
        include_deprecated: bool = True,
        consolidated_only: bool = False,
    ) -> list[dict]:
        """Convert registered tools to Anthropic tool format.

        Args:
            include_deprecated: If False, exclude deprecated tools
            consolidated_only: If True, only include consolidated tools
        """
        tools = []
        for registered in self._tools.values():
            if not include_deprecated and registered.is_deprecated:
                continue
            if consolidated_only and registered.category != "consolidated":
                continue
            tools.append(
                {
                    "name": registered.name,
                    "description": registered.description,
                    "input_schema": registered.parameters_schema,
                }
            )
        return tools

    def to_openai_tools(
        self,
        include_deprecated: bool = True,
        consolidated_only: bool = False,
    ) -> list[dict]:
        """Convert registered tools to OpenAI function calling format.

        Args:
            include_deprecated: If False, exclude deprecated tools
            consolidated_only: If True, only include consolidated tools
        """
        tools = []
        for registered in self._tools.values():
            if not include_deprecated and registered.is_deprecated:
                continue
            if consolidated_only and registered.category != "consolidated":
                continue
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": registered.name,
                        "description": registered.description,
                        "parameters": registered.parameters_schema,
                    },
                }
            )
        return tools

    def mark_deprecated(self, tool_name: str, replacement: str | None = None) -> bool:
        """Mark a tool as deprecated.

        Args:
            tool_name: Name of the tool to deprecate
            replacement: Name of the replacement tool

        Returns:
            True if tool was found and marked, False otherwise
        """
        if tool_name not in self._tools:
            return False

        tool = self._tools[tool_name]
        tool.is_deprecated = True
        tool.replacement = replacement
        tool.deprecation_message = (
            f"'{tool_name}' is deprecated. Use '{replacement}' instead."
            if replacement
            else f"'{tool_name}' is deprecated."
        )
        return True

    def mark_all_deprecated_from_map(self) -> int:
        """Mark all tools in TOOL_DEPRECATION_MAP as deprecated.

        Returns:
            Number of tools marked as deprecated
        """
        count = 0
        for old_name, replacement in TOOL_DEPRECATION_MAP.items():
            if self.mark_deprecated(old_name, replacement):
                count += 1
        return count
