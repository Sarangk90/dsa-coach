"""System prompts and context builders (re-export facade).

Actual implementations live in:
- system_prompt.py: COACH_AGENT_SYSTEM_PROMPT (~740 lines)
- student_context.py: build_student_context + format helpers
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .student_context import (
    _compute_slice_progress,
    _format_activity,
    _format_concepts,
    _format_current_session,
    _format_due_reviews,
    _format_mastery_snapshot,
    _format_mistakes,
    _format_slice_progress,
    _format_wins,
    _get_current_slice,
    build_student_context,
)
from .system_prompt import COACH_AGENT_SYSTEM_PROMPT

if TYPE_CHECKING:
    pass

__all__ = [
    "COACH_AGENT_SYSTEM_PROMPT",
    "build_student_context",
    "get_agent_system_prompt",
    # Private helpers re-exported for test access
    "_compute_slice_progress",
    "_format_activity",
    "_format_concepts",
    "_format_current_session",
    "_format_due_reviews",
    "_format_mastery_snapshot",
    "_format_mistakes",
    "_format_slice_progress",
    "_format_wins",
    "_get_current_slice",
]


def get_agent_system_prompt(
    dashboard_state: dict | None = None, student_context: str | None = None
) -> str:
    """
    Get the system prompt for the coaching agent with student context.

    Args:
        dashboard_state: Dashboard state used as contextual fallback
        student_context: Comprehensive student context string from build_student_context()

    Returns:
        Complete system prompt with student context
    """
    base = COACH_AGENT_SYSTEM_PROMPT

    # Prefer rich student context if available
    if student_context:
        return base + "\n\n" + student_context

    # Fallback to dashboard_state if student_context is unavailable
    if dashboard_state:
        profile = dashboard_state.get("profile", {})
        current = dashboard_state.get("current_quest")
        alerts = dashboard_state.get("alerts", [])

        context = f"""

## CURRENT SESSION CONTEXT
- User: {profile.get("name", "Unknown")}
- Quests Completed: {profile.get("quests_completed", 0)}
- Member Since: {profile.get("created_at", "N/A")[:10]}
- Current Quest: {current["title"] if current else "None"}
- Alerts: {len(alerts)} items needing attention
"""
        return base + context

    return base
