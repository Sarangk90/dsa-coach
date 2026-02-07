"""Regression tests for SDKCoachAgent runtime control flow."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from dsa_coach.agent.sdk_agent import SDKCoachAgent
from dsa_coach.ai import client as ai_client
from dsa_coach.tools.registry import ToolResult as RegistryToolResult


class FakeDB:
    def __init__(self):
        self.session = SimpleNamespace(metadata={})
        self.updated = 0

    async def get_latest_session(self, _user_id: str):
        return self.session

    async def update_session(self, _session) -> None:
        self.updated += 1


class FakeSession:
    def __init__(self):
        self.history: list[dict] = []
        self.user_messages: list[str] = []
        self.assistant_messages: list[dict] = []
        self.tool_calls: list[tuple[str, dict]] = []
        self.tool_results: list[tuple[str, str, bool]] = []

    async def add_user_message(self, content: str):
        self.user_messages.append(content)
        self.history.append({"role": "user", "content": content})
        return SimpleNamespace(content=content)

    def get_messages_for_llm(self):
        return list(self.history)

    async def add_assistant_message(
        self,
        content: str,
        thinking: str | None = None,
        thinking_signature: str | None = None,
    ):
        self.assistant_messages.append(
            {
                "content": content,
                "thinking": thinking,
                "thinking_signature": thinking_signature,
            }
        )
        self.history.append({"role": "assistant", "content": content})
        return SimpleNamespace(content=content)

    async def add_tool_call(self, tool_name: str, tool_args: dict):
        self.tool_calls.append((tool_name, tool_args))
        return SimpleNamespace()

    async def add_tool_result(
        self, tool_name: str, result: str, is_error: bool = False
    ):
        self.tool_results.append((tool_name, result, is_error))
        return SimpleNamespace()


@pytest.mark.asyncio
async def test_run_returns_friendly_error_when_initial_llm_call_fails(monkeypatch):
    agent = SDKCoachAgent(db=FakeDB())
    fake_session = FakeSession()
    monkeypatch.setattr(agent, "session", fake_session)
    agent._token_usage = ai_client.TokenUsage(context_limit=1000)

    async def fail_llm(*_args, **_kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(ai_client, "get_ai_response_with_tools", fail_llm)

    result = await agent.run("hello")

    assert "trouble connecting to the AI service" in result.content
    assert "network down" in (result.error or "")
    assert result.token_usage is agent._token_usage
    assert fake_session.user_messages == ["hello"]
    assert fake_session.assistant_messages == []


@pytest.mark.asyncio
async def test_run_simple_response_updates_tokens_and_records_assistant(monkeypatch):
    agent = SDKCoachAgent(db=FakeDB())
    fake_session = FakeSession()
    monkeypatch.setattr(agent, "session", fake_session)
    agent._token_usage = ai_client.TokenUsage(context_limit=1000)

    async def ok_llm(*_args, **_kwargs):
        return ai_client.LLMResponse(
            content="Final answer",
            input_tokens=123,
            output_tokens=45,
            thinking="internal reasoning",
            thinking_signature="sig_1",
        )

    monkeypatch.setattr(ai_client, "get_ai_response_with_tools", ok_llm)

    reasoning: list[str] = []
    result = await agent.run("help me", on_reasoning=reasoning.append)

    assert result.content == "Final answer"
    assert result.state_updated is False
    assert result.tool_calls_made == []
    assert result.error is None
    assert reasoning == ["internal reasoning"]
    assert agent._token_usage.input_tokens == 123
    assert agent._token_usage.output_tokens == 45
    assert len(fake_session.assistant_messages) == 1
    assert fake_session.assistant_messages[0]["thinking_signature"] == "sig_1"


@pytest.mark.asyncio
async def test_run_tool_loop_uses_fallback_message_when_final_content_empty(
    monkeypatch,
):
    agent = SDKCoachAgent(db=FakeDB())
    fake_session = FakeSession()
    monkeypatch.setattr(agent, "session", fake_session)
    agent._token_usage = ai_client.TokenUsage(context_limit=1000)

    first = ai_client.LLMResponse(
        content="Calling tool now",
        tool_calls=[
            ai_client.ToolCall(
                id="tc1",
                name="start_quest",
                arguments={"quest_id": "q1"},
            )
        ],
        thinking="think-1",
        thinking_signature="sig-1",
    )
    second = ai_client.LLMResponse(content="")
    responses = [first, second]

    async def seq_llm(*_args, **_kwargs):
        return responses.pop(0)

    refreshed = {"count": 0}

    async def fake_refresh_context():
        refreshed["count"] += 1

    async def fake_execute(_tool_calls):
        return [ai_client.ToolResult(tool_use_id="tc1", content='{"ok": true}')], []

    monkeypatch.setattr(ai_client, "get_ai_response_with_tools", seq_llm)
    monkeypatch.setattr(agent, "_execute_tool_calls_with_hooks", fake_execute)
    monkeypatch.setattr(agent, "_refresh_student_context", fake_refresh_context)

    reasoning: list[str] = []
    result = await agent.run("do it", on_reasoning=reasoning.append)

    assert (
        result.content == "I've updated your progress. What would you like to do next?"
    )
    assert result.state_updated is True
    assert result.tool_calls_made == [
        {"name": "start_quest", "args": {"quest_id": "q1"}}
    ]
    assert refreshed["count"] == 1
    assert len(fake_session.assistant_messages) == 0  # final content was empty
    assert reasoning == ["think-1", "Calling tool now"]


@pytest.mark.asyncio
async def test_run_returns_processing_error_when_followup_llm_call_fails(monkeypatch):
    agent = SDKCoachAgent(db=FakeDB())
    fake_session = FakeSession()
    monkeypatch.setattr(agent, "session", fake_session)
    agent._token_usage = ai_client.TokenUsage(context_limit=1000)

    first = ai_client.LLMResponse(
        content="need tools",
        tool_calls=[ai_client.ToolCall(id="tc1", name="list_patterns", arguments={})],
    )
    calls = {"count": 0}

    async def llm_then_fail(*_args, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return first
        raise RuntimeError("followup failure")

    async def fake_execute(_tool_calls):
        return [ai_client.ToolResult(tool_use_id="tc1", content="[]")], []

    monkeypatch.setattr(ai_client, "get_ai_response_with_tools", llm_then_fail)
    monkeypatch.setattr(agent, "_execute_tool_calls_with_hooks", fake_execute)

    result = await agent.run("trigger tool")

    assert "An error occurred while processing" in result.content
    assert "followup failure" in (result.error or "")
    assert result.tool_calls_made == [{"name": "list_patterns", "args": {}}]


@pytest.mark.asyncio
async def test_execute_tool_calls_with_hooks_success_failure_and_exception_paths(
    monkeypatch,
):
    agent = SDKCoachAgent(db=FakeDB())
    fake_session = FakeSession()
    monkeypatch.setattr(agent, "session", fake_session)

    class FakeTools:
        async def execute(self, name: str, **kwargs):
            assert kwargs["db"] is agent.db
            assert kwargs["user_id"] == agent.user_id
            if name == "ok_tool":
                return RegistryToolResult(success=True, data={"value": 1})
            if name == "bad_tool":
                return RegistryToolResult(success=False, error="bad input")
            raise RuntimeError("boom")

    applied: list[tuple[str, bool]] = []

    async def fake_apply(tool_name: str, result):
        applied.append((tool_name, result.success))

    monkeypatch.setattr(agent, "tools", FakeTools())
    monkeypatch.setattr(agent, "_apply_workflow_hook", fake_apply)

    tool_calls = [
        SimpleNamespace(id="t1", name="ok_tool", arguments={"x": 1}),
        SimpleNamespace(id="t2", name="bad_tool", arguments={}),
        SimpleNamespace(id="t3", name="explode_tool", arguments={}),
    ]

    results, errors = await agent._execute_tool_calls_with_hooks(tool_calls)

    assert len(results) == 3
    assert results[0].tool_use_id == "t1" and results[0].is_error is False
    assert '"value": 1' in results[0].content
    assert results[1].is_error is True
    assert results[1].content == "Error: bad input"
    assert results[2].is_error is True
    assert "Tool execution failed: boom" in results[2].content

    assert errors == [
        {"tool": "bad_tool", "error": "bad input"},
        {"tool": "explode_tool", "error": "boom"},
    ]
    # Hook applies only for tool execution that reached result object.
    assert applied == [("ok_tool", True), ("bad_tool", False)]

    assert [name for name, _ in fake_session.tool_calls] == [
        "ok_tool",
        "bad_tool",
        "explode_tool",
    ]
    assert len(fake_session.tool_results) == 3
