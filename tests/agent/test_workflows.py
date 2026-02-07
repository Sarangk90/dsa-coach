"""Regression tests for workflow state machine invariants."""

from __future__ import annotations

from dsa_coach.agent.workflows import (
    SessionMode,
    WorkflowManager,
    WorkflowState,
    get_mode_description,
    is_valid_transition,
)


def test_workflow_state_round_trip_and_legacy_key_support():
    state = WorkflowState(mode=SessionMode.LEARNING, current_pattern="graphs")
    payload = state.to_dict()
    restored = WorkflowState.from_dict(payload)

    assert restored.mode == SessionMode.LEARNING
    assert restored.current_pattern == "graphs"

    legacy = WorkflowState.from_dict(
        {
            "mode": "practicing",
            "start_confidence": 42,  # Legacy key still supported
            "started_at": "not-a-date",
        }
    )
    assert legacy.mode == SessionMode.PRACTICING
    assert legacy.start_progress == 42


def test_workflow_manager_transitions_and_progress_gain():
    manager = WorkflowManager()
    assert manager.state.mode == SessionMode.GREETING

    manager.start_quest("q1", "arrays_hashing", progress=30)
    assert SessionMode(manager.state.mode) == SessionMode.PRACTICING
    assert manager.state.current_quest == "q1"
    assert manager.get_progress_gain(45) == 15

    manager.complete_quest()
    assert manager.state.mode == SessionMode.GREETING
    assert manager.state.current_quest is None

    manager.start_learning("graphs", progress=10)
    assert manager.state.mode == SessionMode.LEARNING
    assert manager.state.current_pattern == "graphs"

    manager.start_review()
    assert manager.state.mode == SessionMode.REVIEWING

    manager.start_mock_interview()
    assert manager.state.mode == SessionMode.SIMULATING


def test_workflow_note_suggestion_rules_cover_both_threshold_paths():
    manager = WorkflowManager()
    manager.start_learning("trees", progress=20)

    suggest, reason = manager.should_suggest_note_creation(current_progress=45)
    assert suggest is True
    assert "Progress gained" in reason

    manager.state.start_progress = 40
    manager.state.message_count = 15
    suggest, reason = manager.should_suggest_note_creation(current_progress=45)
    assert suggest is True
    assert "Significant learning session" in reason

    manager.state.message_count = 3
    suggest, reason = manager.should_suggest_note_creation(current_progress=45)
    assert suggest is False
    assert "not met" in reason


def test_tool_availability_and_transition_validity_contracts():
    manager = WorkflowManager()
    available = manager.get_available_tools()

    assert "get_dashboard" in available
    assert "start_quest" in available
    assert manager.is_tool_available("list_patterns") is True
    assert manager.is_tool_available("nonexistent_tool") is False

    assert is_valid_transition(SessionMode.GREETING, SessionMode.PRACTICING) is True
    assert is_valid_transition(SessionMode.SIMULATING, SessionMode.LEARNING) is False


def test_mode_description_has_fallback_for_unknown_mode():
    assert "Welcome state" in get_mode_description(SessionMode.GREETING)
    assert get_mode_description("invalid") == "Unknown mode"
