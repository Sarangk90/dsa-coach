"""Unit tests for AI client routing and payload conversion logic."""

from __future__ import annotations

import pytest

from dsa_coach.ai import client


def test_token_usage_properties_and_display():
    usage = client.TokenUsage(
        input_tokens=150000, output_tokens=5000, context_limit=200000
    )

    assert usage.total_tokens == 155000
    assert usage.percentage_used == 75.0
    assert usage.is_warning_threshold is True
    assert usage.format_display() == "150,000/200,000 (75.0%)"


def test_check_ai_available_prefers_anthropic_then_openai(monkeypatch):
    monkeypatch.setattr(client, "ANTHROPIC_AVAILABLE", True)
    monkeypatch.setattr(client, "ANTHROPIC_API_KEY", "anthropic-key")
    monkeypatch.setattr(client, "OPENAI_AVAILABLE", True)
    monkeypatch.setattr(client, "OPENAI_API_KEY", "openai-key")
    assert client.check_ai_available() == (True, "Anthropic API available")

    monkeypatch.setattr(client, "ANTHROPIC_AVAILABLE", False)
    monkeypatch.setattr(client, "ANTHROPIC_API_KEY", None)
    assert client.check_ai_available() == (True, "OpenAI API available")


def test_get_ai_response_routes_to_openai_with_system_message(monkeypatch):
    monkeypatch.setattr(client, "PREFERRED_PROVIDER", "openai")
    monkeypatch.setattr(client, "OPENAI_AVAILABLE", True)
    monkeypatch.setattr(client, "OPENAI_API_KEY", "key")
    monkeypatch.setattr(client, "ANTHROPIC_AVAILABLE", False)
    monkeypatch.setattr(client, "ANTHROPIC_API_KEY", None)

    captured = {}

    def fake_call_openai(messages, max_tokens):
        captured["messages"] = messages
        captured["max_tokens"] = max_tokens
        return "openai response"

    monkeypatch.setattr(client, "call_openai", fake_call_openai)

    result = client.get_ai_response(
        user_message="hello",
        system_prompt="system prompt",
        max_tokens=321,
        conversation_history=[{"role": "assistant", "content": "prior"}],
    )

    assert result == "openai response"
    assert captured["max_tokens"] == 321
    assert captured["messages"][0] == {"role": "system", "content": "system prompt"}
    assert captured["messages"][-1] == {"role": "user", "content": "hello"}


def test_get_ai_response_raises_when_no_provider_available(monkeypatch):
    monkeypatch.setattr(client, "PREFERRED_PROVIDER", "anthropic")
    monkeypatch.setattr(client, "OPENAI_AVAILABLE", False)
    monkeypatch.setattr(client, "OPENAI_API_KEY", None)
    monkeypatch.setattr(client, "ANTHROPIC_AVAILABLE", False)
    monkeypatch.setattr(client, "ANTHROPIC_API_KEY", None)

    with pytest.raises(RuntimeError, match="No LLM provider available"):
        client.get_ai_response("hi", "system")


@pytest.mark.asyncio
async def test_get_ai_response_with_tools_openai_conversion_path(monkeypatch):
    monkeypatch.setattr(client, "PREFERRED_PROVIDER", "openai")
    monkeypatch.setattr(client, "OPENAI_AVAILABLE", True)
    monkeypatch.setattr(client, "OPENAI_API_KEY", "key")
    monkeypatch.setattr(client, "ANTHROPIC_AVAILABLE", False)
    monkeypatch.setattr(client, "ANTHROPIC_API_KEY", None)

    captured = {}

    async def fake_call_openai_with_tools(messages, tools, max_tokens):
        captured["messages"] = messages
        captured["tools"] = tools
        captured["max_tokens"] = max_tokens
        return client.LLMResponse(content="ok")

    monkeypatch.setattr(client, "call_openai_with_tools", fake_call_openai_with_tools)

    response = await client.get_ai_response_with_tools(
        messages=[
            {"role": "user", "content": "hello"},
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "working"},
                    {
                        "type": "tool_use",
                        "id": "call_1",
                        "name": "get_dashboard",
                        "input": {"foo": "bar"},
                    },
                ],
            },
        ],
        system_prompt="system",
        tools=[
            {
                "name": "get_dashboard",
                "description": "dash",
                "input_schema": {"type": "object", "properties": {}},
            }
        ],
        max_tokens=200,
    )

    assert response.content == "ok"
    assert captured["messages"][0] == {"role": "system", "content": "system"}
    assert captured["messages"][1]["role"] == "user"
    assert captured["messages"][2]["role"] == "assistant"
    assert (
        captured["messages"][2]["tool_calls"][0]["function"]["name"] == "get_dashboard"
    )
    assert captured["tools"][0]["type"] == "function"
    assert captured["max_tokens"] == 200


def test_convert_tools_to_openai_and_messages_to_openai():
    converted_tools = client._convert_tools_to_openai(  # noqa: SLF001 - testing helper
        [
            {
                "name": "list_patterns",
                "description": "List patterns",
                "input_schema": {
                    "type": "object",
                    "properties": {"mode": {"type": "string"}},
                },
            },
            {"name": "empty_schema_tool"},
        ]
    )
    assert converted_tools[0]["function"]["name"] == "list_patterns"
    assert converted_tools[1]["function"]["parameters"]["type"] == "object"

    converted_messages = client._convert_messages_to_openai(  # noqa: SLF001 - testing helper
        [
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "I called a tool"},
                    {
                        "type": "tool_use",
                        "id": "t1",
                        "name": "list_patterns",
                        "input": {"mode": "fast_track"},
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "t1",
                        "content": '{"ok":true}',
                    }
                ],
            },
        ]
    )
    assert converted_messages[0]["role"] == "assistant"
    assert converted_messages[0]["tool_calls"][0]["id"] == "t1"
    assert converted_messages[1]["role"] == "tool"
    assert converted_messages[1]["tool_call_id"] == "t1"


def test_format_tool_result_helpers():
    results = [
        client.ToolResult(tool_use_id="x1", content="ok", is_error=False),
        client.ToolResult(tool_use_id="x2", content="boom", is_error=True),
    ]

    anthropic = client.format_tool_result_for_anthropic(results)
    assert anthropic[0]["type"] == "tool_result"
    assert anthropic[1]["is_error"] is True

    openai = client.format_tool_result_for_openai(results)
    assert openai == [
        {"role": "tool", "tool_call_id": "x1", "content": "ok"},
        {"role": "tool", "tool_call_id": "x2", "content": "boom"},
    ]
