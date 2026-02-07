"""Tests for agent hook behavior and registry wiring."""

from typing import Any, cast

import pytest

from dsa_coach.agent.hooks import (
    HookRegistry,
    LearningHook,
    QuestCompletionHook,
    SessionEndHook,
    create_default_hook_registry,
)
from dsa_coach.tools.registry import ToolResult


@pytest.mark.asyncio
async def test_quest_completion_hook_should_execute_only_for_successful_trigger_tools():
    hook = QuestCompletionHook()

    assert await hook.should_execute("complete_quest", ToolResult(success=True)) is True
    assert (
        await hook.should_execute("mark_quest_complete", ToolResult(success=True))
        is True
    )
    assert (
        await hook.should_execute("complete_quest", ToolResult(success=False)) is False
    )
    assert await hook.should_execute("unknown_tool", ToolResult(success=True)) is False


@pytest.mark.asyncio
async def test_quest_completion_hook_returns_not_executed_when_data_missing():
    hook = QuestCompletionHook()

    result = await hook.execute(
        db=None, user_id="default", tool_result=ToolResult(data=None)
    )

    assert result.executed is False
    assert result.action_taken == "No data in result"


@pytest.mark.asyncio
async def test_quest_completion_hook_collects_milestone_and_note_actions():
    hook = QuestCompletionHook()
    tool_result = ToolResult(
        success=True,
        data={
            "pattern_id": "sliding_window",
            "pattern_progress": 85,
            "milestone_awarded": {"description": "Mastered Sliding Window"},
            "note_suggestion": {"reason": "Strong recent progress"},
        },
    )

    result = await hook.execute(db=None, user_id="default", tool_result=tool_result)

    assert result.executed is True
    assert result.action_taken is not None
    data = cast(dict[str, Any], result.data)
    assert "Milestone awarded: Mastered Sliding Window" in result.action_taken
    assert "Note creation suggested" in result.action_taken
    assert data["pattern_id"] == "sliding_window"
    assert data["progress"] == 85
    assert len(data["actions"]) == 2


@pytest.mark.asyncio
async def test_learning_hook_flags_recurring_mistakes_and_advice():
    hook = LearningHook()
    tool_result = ToolResult(
        success=True,
        data={
            "type": "mistake",
            "recurrence_count": 4,
            "coaching_advice": "Practice boundary checks.",
        },
    )

    result = await hook.execute(db=None, user_id="default", tool_result=tool_result)

    assert result.executed is True
    assert result.action_taken is not None
    assert "Recurring mistake detected (4x)" in result.action_taken
    assert "Advice: Practice boundary checks." in result.action_taken


@pytest.mark.asyncio
async def test_learning_hook_flags_repeated_explanations():
    hook = LearningHook()
    tool_result = ToolResult(
        success=True,
        data={"type": "concept_taught", "explanation_count": 3},
    )

    result = await hook.execute(db=None, user_id="default", tool_result=tool_result)

    assert result.executed is True
    assert result.action_taken is not None
    assert (
        "Concept explained 3x - try different teaching approach" in result.action_taken
    )


@pytest.mark.asyncio
async def test_learning_hook_defaults_to_learning_recorded_without_extra_actions():
    hook = LearningHook()
    tool_result = ToolResult(success=True, data={"type": "concept_understood"})

    result = await hook.execute(db=None, user_id="default", tool_result=tool_result)

    assert result.executed is True
    assert result.action_taken == "Learning recorded (concept_understood)"
    data = cast(dict[str, Any], result.data)
    assert data["actions"] == []


@pytest.mark.asyncio
async def test_session_end_hook_should_execute_is_always_false():
    hook = SessionEndHook()
    assert await hook.should_execute("anything", ToolResult(success=True)) is False


@pytest.mark.asyncio
async def test_session_end_hook_suggests_note_and_progress_summary(monkeypatch):
    hook = SessionEndHook()

    def fake_should_create_note(pattern, progress, session_messages, progress_gain):
        assert pattern == "two_pointers"
        assert progress == 55
        assert session_messages == 18
        assert progress_gain == 25
        return True, "Milestone-worthy session"

    monkeypatch.setattr(
        "dsa_coach.agent.hooks.should_create_note", fake_should_create_note
    )

    result = await hook.execute(
        db=None,
        user_id="default",
        session_data={
            "current_pattern": "two_pointers",
            "start_progress": 30,
            "current_progress": 55,
            "message_count": 18,
        },
    )

    assert result.executed is True
    assert result.action_taken is not None
    data = cast(dict[str, Any], result.data)
    assert "Note creation suggested: Milestone-worthy session" in result.action_taken
    assert "Progress increased by 25%" in result.action_taken
    assert "Session had 18 messages" in result.action_taken
    assert data["progress_gain"] == 25


@pytest.mark.asyncio
async def test_session_end_hook_returns_generic_message_when_no_actions():
    hook = SessionEndHook()

    result = await hook.execute(
        db=None,
        user_id="default",
        session_data={
            "current_pattern": None,
            "start_progress": 10,
            "current_progress": 10,
            "message_count": 0,
        },
    )

    assert result.executed is True
    assert result.action_taken == "Session ended"
    data = cast(dict[str, Any], result.data)
    assert data["actions"] == []


@pytest.mark.asyncio
async def test_hook_registry_executes_only_matching_hooks():
    registry = HookRegistry()
    registry.register_defaults()

    results = await registry.execute_hooks(
        db=None,
        user_id="default",
        tool_name="complete_quest",
        tool_result=ToolResult(success=True, data={"pattern_id": "graphs"}),
    )

    assert len(results) == 1
    assert results[0].executed is True
    data = cast(dict[str, Any], results[0].data)
    assert data["pattern_id"] == "graphs"


@pytest.mark.asyncio
async def test_hook_registry_session_end_returns_not_executed_if_not_registered():
    registry = HookRegistry()

    result = await registry.execute_session_end(
        db=None,
        user_id="default",
        session_data={},
    )

    assert result.executed is False
    assert result.action_taken == "No session end hook registered"


def test_create_default_hook_registry_registers_expected_hooks():
    registry = create_default_hook_registry()

    assert len(registry._hooks) == 3  # Internal registry contract
    assert isinstance(registry._hooks[0], QuestCompletionHook)
    assert isinstance(registry._hooks[1], LearningHook)
    assert isinstance(registry._hooks[2], SessionEndHook)
