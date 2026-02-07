"""Workflow state machine for DSA Coach agent.

This module defines session modes and workflow states to guide
tool availability and agent behavior throughout a coaching session.

Session Modes:
- GREETING: Initial state, show dashboard
- PRACTICING: Working on a quest (problem-solving)
- LEARNING: Teaching a pattern (concept explanation)
- REVIEWING: Spaced repetition (review practice)
- SIMULATING: Mock interview mode
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SessionMode(str, Enum):
    """Session modes representing different coaching workflows."""

    GREETING = "greeting"
    PRACTICING = "practicing"
    LEARNING = "learning"
    REVIEWING = "reviewing"
    SIMULATING = "simulating"


# Tools available in each session mode
TOOL_AVAILABILITY: dict[SessionMode, set[str]] = {
    SessionMode.GREETING: {
        "get_dashboard",
        "list_patterns",
        "get_progress_summary",
        "start_quest",
    },
    SessionMode.PRACTICING: {
        "get_dashboard",
        "complete_quest",
        "get_hint",
        "manage_solution",
        "review_code",
        "record_learning",
        "get_teaching_context",
    },
    SessionMode.LEARNING: {
        "get_dashboard",
        "diagnose_understanding",
        "record_learning",
        "get_teaching_context",
        "get_pattern_details",
        "start_quest",  # To transition to practice
    },
    SessionMode.REVIEWING: {
        "get_dashboard",
        "get_progress_summary",
        "record_review",
        "get_hint",
        "record_learning",
    },
    SessionMode.SIMULATING: {
        "get_dashboard",
        "get_hint",
        "record_learning",
        "complete_quest",
    },
}

# Universal tools available in all modes
# Note: Obsidian note tools are now provided via MCP (not in this set)
UNIVERSAL_TOOLS: set[str] = {
    "get_dashboard",
    "list_patterns",
    "get_pattern_details",
}


@dataclass
class WorkflowState:
    """Current workflow state for a session."""

    mode: SessionMode = SessionMode.GREETING
    current_pattern: str | None = None
    current_quest: str | None = None
    start_progress: int = 0
    message_count: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for session metadata storage."""
        return {
            "mode": self.mode.value,
            "current_pattern": self.current_pattern,
            "current_quest": self.current_quest,
            "start_progress": self.start_progress,
            "message_count": self.message_count,
            "started_at": self.started_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowState:
        """Create from dictionary (session metadata)."""
        mode = SessionMode(data.get("mode", "greeting"))
        started_at = data.get("started_at")
        if isinstance(started_at, str):
            try:
                started_at = datetime.fromisoformat(started_at)
            except ValueError:
                started_at = datetime.now()
        else:
            started_at = datetime.now()

        return cls(
            mode=mode,
            current_pattern=data.get("current_pattern"),
            current_quest=data.get("current_quest"),
            start_progress=data.get("start_progress", data.get("start_confidence", 0)),
            message_count=data.get("message_count", 0),
            started_at=started_at,
            metadata=data.get("metadata", {}),
        )


class WorkflowManager:
    """Manages workflow state transitions and tool availability."""

    def __init__(self, initial_state: WorkflowState | None = None):
        self.state = initial_state or WorkflowState()

    def get_available_tools(self) -> set[str]:
        """Get tools available in current mode."""
        mode_tools = TOOL_AVAILABILITY.get(self.state.mode, set())
        return mode_tools | UNIVERSAL_TOOLS

    def is_tool_available(self, tool_name: str) -> bool:
        """Check if a tool is available in current mode."""
        return tool_name in self.get_available_tools()

    def transition_to(self, new_mode: SessionMode) -> None:
        """Transition to a new session mode."""
        self.state.mode = new_mode

    def start_quest(self, quest_id: str, pattern_id: str, progress: int = 0) -> None:
        """Start working on a quest."""
        self.state.mode = SessionMode.PRACTICING
        self.state.current_quest = quest_id
        self.state.current_pattern = pattern_id
        self.state.start_progress = progress

    def complete_quest(self) -> None:
        """Complete current quest."""
        self.state.current_quest = None
        self.state.mode = SessionMode.GREETING

    def start_learning(self, pattern_id: str, progress: int = 0) -> None:
        """Start learning a pattern."""
        self.state.mode = SessionMode.LEARNING
        self.state.current_pattern = pattern_id
        self.state.start_progress = progress

    def start_review(self) -> None:
        """Start spaced repetition review."""
        self.state.mode = SessionMode.REVIEWING

    def start_mock_interview(self) -> None:
        """Start mock interview simulation."""
        self.state.mode = SessionMode.SIMULATING

    def increment_message_count(self) -> int:
        """Increment and return message count."""
        self.state.message_count += 1
        return self.state.message_count

    def get_progress_gain(self, current_progress: int) -> int:
        """Calculate progress gain since session start."""
        return current_progress - self.state.start_progress

    def should_suggest_note_creation(
        self,
        current_progress: int,
        min_progress_gain: int = 20,
        min_messages: int = 15,
    ) -> tuple[bool, str]:
        """Check if note creation should be suggested.

        Returns:
            Tuple of (should_create, reason)
        """
        progress_gain = self.get_progress_gain(current_progress)

        if progress_gain >= min_progress_gain:
            return True, f"Progress gained {progress_gain}% this session"

        if self.state.message_count >= min_messages:
            return (
                True,
                f"Significant learning session ({self.state.message_count} messages)",
            )

        return False, "Note creation criteria not met"


# Workflow transition rules
VALID_TRANSITIONS: dict[SessionMode, set[SessionMode]] = {
    SessionMode.GREETING: {
        SessionMode.PRACTICING,
        SessionMode.LEARNING,
        SessionMode.REVIEWING,
        SessionMode.SIMULATING,
    },
    SessionMode.PRACTICING: {
        SessionMode.GREETING,
        SessionMode.LEARNING,  # If stuck, can switch to learning
    },
    SessionMode.LEARNING: {
        SessionMode.GREETING,
        SessionMode.PRACTICING,  # Transition to practice after learning
    },
    SessionMode.REVIEWING: {
        SessionMode.GREETING,
        SessionMode.PRACTICING,  # If review reveals need for practice
    },
    SessionMode.SIMULATING: {
        SessionMode.GREETING,
    },
}


def is_valid_transition(from_mode: SessionMode, to_mode: SessionMode) -> bool:
    """Check if a transition between modes is valid."""
    valid = VALID_TRANSITIONS.get(from_mode, set())
    return to_mode in valid


def get_mode_description(mode: SessionMode) -> str:
    """Get human-readable description of a mode."""
    descriptions = {
        SessionMode.GREETING: "Welcome state - reviewing dashboard and choosing activity",
        SessionMode.PRACTICING: "Problem-solving mode - working on a specific quest",
        SessionMode.LEARNING: "Teaching mode - learning concepts within a pattern",
        SessionMode.REVIEWING: "Spaced repetition mode - reviewing previously solved problems",
        SessionMode.SIMULATING: "Mock interview mode - realistic interview simulation",
    }
    return descriptions.get(mode, "Unknown mode")
