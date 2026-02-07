"""Unit tests for SDKCoachAgent internal workflow hooks.

These tests avoid real model/network calls and validate state transitions
that are critical during refactors.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest

from dsa_coach.agent.sdk_agent import SDKCoachAgent
from dsa_coach.agent.workflows import SessionMode
from dsa_coach.tools.registry import ToolResult


class FakeDB:
    def __init__(self):
        self.session = SimpleNamespace(metadata={})
        self.updated_sessions: list[dict] = []

    async def get_latest_session(self, user_id: str):
        return self.session

    async def update_session(self, session):
        self.updated_sessions.append(dict(session.metadata))


@pytest.mark.asyncio
async def test_apply_workflow_hook_start_and_complete_quest_transitions():
    db = FakeDB()
    agent = SDKCoachAgent(db=db)

    await agent._apply_workflow_hook(
        "start_quest",
        ToolResult(success=True, data={"quest_id": "q1", "pattern_id": "graphs"}),
    )
    assert agent.workflow.state.mode == SessionMode.PRACTICING
    assert agent.workflow.state.current_quest == "q1"
    assert agent.workflow.state.current_pattern == "graphs"

    await agent._apply_workflow_hook(
        "complete_quest",
        ToolResult(success=True, data={"quest_id": "q1"}),
    )
    assert SessionMode(agent.workflow.state.mode) == SessionMode.GREETING
    assert agent.workflow.state.current_quest is None


@pytest.mark.asyncio
async def test_apply_workflow_hook_diagnose_understanding_enters_learning():
    db = FakeDB()
    agent = SDKCoachAgent(db=db)

    await agent._apply_workflow_hook(
        "diagnose_understanding",
        ToolResult(success=True, data={"pattern_id": "dynamic_programming"}),
    )

    assert agent.workflow.state.mode == SessionMode.LEARNING
    assert agent.workflow.state.current_pattern == "dynamic_programming"


@pytest.mark.asyncio
async def test_apply_workflow_hook_ignores_failed_or_empty_results():
    db = FakeDB()
    agent = SDKCoachAgent(db=db)
    original_mode = agent.workflow.state.mode

    await agent._apply_workflow_hook(
        "start_quest", ToolResult(success=False, data={"quest_id": "q1"})
    )
    await agent._apply_workflow_hook("start_quest", ToolResult(success=True, data=None))

    assert agent.workflow.state.mode == original_mode
    assert agent.workflow.state.current_quest is None


@pytest.mark.asyncio
async def test_post_tool_hook_updates_workflow_and_persists_metadata():
    db = FakeDB()
    agent = SDKCoachAgent(db=db)

    hook = await agent._create_post_tool_hook()

    await hook(
        {
            "tool_name": "start_quest",
            "tool_response": {"content": {"quest_id": "q2", "pattern_id": "trees"}},
        },
        "t1",
        cast(Any, None),  # HookContext is not used in implementation
    )

    assert agent.workflow.state.mode == SessionMode.PRACTICING
    assert agent.workflow.state.current_quest == "q2"
    assert db.updated_sessions
    assert db.updated_sessions[-1]["mode"] == SessionMode.PRACTICING.value


@pytest.mark.asyncio
async def test_post_tool_hook_handles_json_string_and_bad_json():
    db = FakeDB()
    agent = SDKCoachAgent(db=db)
    hook = await agent._create_post_tool_hook()

    await hook(
        {
            "tool_name": "diagnose_understanding",
            "tool_response": {
                "content": '{"pattern_id":"graphs"}',
            },
        },
        "t2",
        cast(Any, None),
    )
    assert agent.workflow.state.mode == SessionMode.LEARNING
    assert agent.workflow.state.current_pattern == "graphs"

    # Bad JSON should not crash or alter state unexpectedly.
    await hook(
        {
            "tool_name": "start_quest",
            "tool_response": {"content": "{bad json"},
        },
        "t3",
        cast(Any, None),
    )
    # State remains whatever was last valid transition.
    assert agent.workflow.state.mode == SessionMode.LEARNING
