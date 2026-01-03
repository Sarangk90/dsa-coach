"""Tool registry for DSA Coach agent.

Provides a decorator-based registry system for agent tools
and utilities for converting to LLM-compatible tool schemas.
"""

import inspect
from typing import Any, Callable, Optional, get_type_hints
from functools import wraps
from pydantic import BaseModel, Field, create_model


# Global registry of all tools
_TOOL_REGISTRY: dict[str, "RegisteredTool"] = {}


class ToolResult(BaseModel):
    """Standard result from a tool execution."""
    
    success: bool = True
    data: Any = None
    message: Optional[str] = None
    error: Optional[str] = None


class RegisteredTool(BaseModel):
    """Metadata about a registered tool."""
    
    model_config = {"arbitrary_types_allowed": True}
    
    name: str
    description: str
    category: str
    func: Callable = Field(exclude=True)
    parameters_schema: dict = Field(default_factory=dict)


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
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
            if param_type == int:
                json_type = "integer"
            elif param_type == float:
                json_type = "number"
            elif param_type == bool:
                json_type = "boolean"
            elif param_type == list:
                json_type = "array"
            elif param_type == dict:
                json_type = "object"
            
            prop = {"type": json_type}
            
            # Add description from docstring if available
            if func.__doc__:
                # Try to extract parameter description from docstring
                doc_lines = func.__doc__.split("\n")
                for line in doc_lines:
                    if f":param {param_name}:" in line or f"Args:" in line:
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
        
        wrapper._tool_info = registered
        return wrapper
    
    return decorator


class ToolRegistry:
    """Registry for managing and executing agent tools."""
    
    def __init__(self):
        self._tools = _TOOL_REGISTRY
    
    def get_tool(self, name: str) -> Optional[RegisteredTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self, category: Optional[str] = None) -> list[RegisteredTool]:
        """List all registered tools, optionally filtered by category."""
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools
    
    def list_categories(self) -> list[str]:
        """Get all unique tool categories."""
        return list(set(t.category for t in self._tools.values()))
    
    async def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name with given arguments."""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found",
            )
        
        try:
            result = await tool.func(**kwargs)
            if isinstance(result, ToolResult):
                return result
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}",
            )
    
    def to_anthropic_tools(self) -> list[dict]:
        """Convert registered tools to Anthropic tool format."""
        tools = []
        for registered in self._tools.values():
            tools.append({
                "name": registered.name,
                "description": registered.description,
                "input_schema": registered.parameters_schema,
            })
        return tools
    
    def to_openai_tools(self) -> list[dict]:
        """Convert registered tools to OpenAI function calling format."""
        tools = []
        for registered in self._tools.values():
            tools.append({
                "type": "function",
                "function": {
                    "name": registered.name,
                    "description": registered.description,
                    "parameters": registered.parameters_schema,
                },
            })
        return tools

