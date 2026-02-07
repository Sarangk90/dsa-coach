"""Regression tests for tool registry contracts."""

from __future__ import annotations

import uuid

import pytest

from dsa_coach.tools.registry import _TOOL_REGISTRY, ToolRegistry, tool


@pytest.mark.asyncio
async def test_tool_decorator_builds_schema_and_execute_filters_kwargs():
    name = f"test_tool_{uuid.uuid4().hex[:8]}"

    @tool(name=name, description="test tool", category="test")
    async def sample_tool(
        required_name: str, count: int, enabled: bool = False, db=None
    ):
        return {"required_name": required_name, "count": count, "enabled": enabled}

    try:
        registry = ToolRegistry()
        registered = registry.get_tool(name)
        assert registered is not None
        assert registered.parameters_schema["required"] == ["required_name", "count"]
        assert (
            registered.parameters_schema["properties"]["required_name"]["type"]
            == "string"
        )
        assert registered.parameters_schema["properties"]["count"]["type"] == "integer"
        assert (
            registered.parameters_schema["properties"]["enabled"]["type"] == "boolean"
        )
        assert "db" not in registered.parameters_schema["properties"]

        result = await registry.execute(
            name,
            required_name="alice",
            count=3,
            enabled=True,
            extra_ignored="value",
        )
        assert result.success
        assert result.data == {"required_name": "alice", "count": 3, "enabled": True}
    finally:
        _TOOL_REGISTRY.pop(name, None)


@pytest.mark.asyncio
async def test_registry_execute_handles_unknown_and_tool_exceptions():
    registry = ToolRegistry()
    missing = await registry.execute("definitely_missing_tool")
    assert missing.success is False
    assert "not found" in (missing.error or "")

    name = f"test_error_tool_{uuid.uuid4().hex[:8]}"

    @tool(name=name, description="error tool", category="test")
    async def exploding_tool(required_param: str):
        raise RuntimeError(f"boom: {required_param}")

    try:
        failed = await registry.execute(name, required_param="x")
        assert failed.success is False
        assert "Tool execution failed: boom: x" in (failed.error or "")
    finally:
        _TOOL_REGISTRY.pop(name, None)


@pytest.mark.asyncio
async def test_registry_conversion_formats_respect_category_filter():
    name = f"test_convert_tool_{uuid.uuid4().hex[:8]}"

    @tool(name=name, description="convert me", category="test")
    async def convert_tool(value: str):
        return {"value": value}

    try:
        registry = ToolRegistry()
        anthropic_all = registry.to_anthropic_tools()
        openai_all = registry.to_openai_tools()

        assert any(t["name"] == name for t in anthropic_all)
        assert any(t["function"]["name"] == name for t in openai_all)

        anthropic_consolidated = registry.to_anthropic_tools(consolidated_only=True)
        openai_consolidated = registry.to_openai_tools(consolidated_only=True)

        assert all(t["name"] != name for t in anthropic_consolidated)
        assert all(t["function"]["name"] != name for t in openai_consolidated)
    finally:
        _TOOL_REGISTRY.pop(name, None)
