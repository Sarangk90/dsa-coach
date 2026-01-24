"""Hook utilities for DSA Coach agent.

This module provides hook classes and utilities for deterministic
post-tool execution actions. Hooks ensure that important follow-up
actions (logging, milestones, note suggestions) never get forgotten.

Hook Types:
- QuestCompletionHook: Runs after quest completion
- LearningHook: Runs after learning/teaching events
- SessionEndHook: Runs when session ends
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ..obsidian.analyzer import should_create_note
from ..storage.db import Database
from ..tools.registry import ToolResult


@dataclass
class HookResult:
    """Result from a hook execution."""

    executed: bool = True
    action_taken: str | None = None
    data: dict[str, Any] | None = None
    error: str | None = None


class Hook(ABC):
    """Base class for all hooks."""

    @abstractmethod
    async def should_execute(self, tool_name: str, tool_result: ToolResult) -> bool:
        """Check if this hook should execute for the given tool result."""
        pass

    @abstractmethod
    async def execute(
        self, db: Database, user_id: str, tool_result: ToolResult
    ) -> HookResult:
        """Execute the hook action."""
        pass


class QuestCompletionHook(Hook):
    """Hook that runs after quest completion.

    Actions:
    1. Log session activity (always)
    2. Check for pattern mastery milestone (if progress >= 80)
    3. Suggest note creation (if progress >= 70)
    """

    def __init__(self):
        self.trigger_tools = {"complete_quest", "mark_quest_complete"}

    async def should_execute(self, tool_name: str, tool_result: ToolResult) -> bool:
        return tool_name in self.trigger_tools and tool_result.success

    async def execute(
        self, db: Database, user_id: str, tool_result: ToolResult
    ) -> HookResult:
        """Execute quest completion hooks.

        Note: Most hooks are now built INTO the complete_quest tool itself.
        This hook provides any additional cross-cutting concerns.
        """
        if not tool_result.data:
            return HookResult(executed=False, action_taken="No data in result")

        data = tool_result.data
        pattern_id = data.get("pattern_id")
        pattern_progress = data.get("pattern_progress", 0)

        actions = []

        # The complete_quest tool already handles:
        # - activity_logged
        # - milestone_awarded
        # - note_suggestion

        # This hook can provide additional actions if needed
        # For example, updating external systems, sending notifications, etc.

        if data.get("milestone_awarded"):
            actions.append(
                f"Milestone awarded: {data['milestone_awarded'].get('description')}"
            )

        if data.get("note_suggestion"):
            actions.append("Note creation suggested")

        return HookResult(
            executed=True,
            action_taken="; ".join(actions) if actions else "Quest completed",
            data={
                "pattern_id": pattern_id,
                "progress": pattern_progress,
                "actions": actions,
            },
        )


class LearningHook(Hook):
    """Hook that runs after learning/teaching events.

    Actions:
    1. Track recurring mistakes
    2. Update concept mastery
    3. Adjust teaching approach based on history
    """

    def __init__(self):
        self.trigger_tools = {"record_learning", "record_mistake", "record_teaching"}

    async def should_execute(self, tool_name: str, tool_result: ToolResult) -> bool:
        return tool_name in self.trigger_tools and tool_result.success

    async def execute(
        self, db: Database, user_id: str, tool_result: ToolResult
    ) -> HookResult:
        """Execute learning hooks."""
        if not tool_result.data:
            return HookResult(executed=False, action_taken="No data in result")

        data = tool_result.data
        learning_type = data.get("type")
        actions = []

        if learning_type == "mistake":
            recurrence_count = data.get("recurrence_count", 1)
            if recurrence_count >= 3:
                actions.append(
                    f"Recurring mistake detected ({recurrence_count}x) - "
                    "consider focused practice"
                )

        elif learning_type == "concept_taught":
            explanation_count = data.get("explanation_count", 1)
            if explanation_count >= 3:
                actions.append(
                    f"Concept explained {explanation_count}x - "
                    "try different teaching approach"
                )

        if data.get("coaching_advice"):
            actions.append(f"Advice: {data['coaching_advice']}")

        return HookResult(
            executed=True,
            action_taken="; ".join(actions)
            if actions
            else f"Learning recorded ({learning_type})",
            data={"type": learning_type, "actions": actions},
        )


class SessionEndHook(Hook):
    """Hook that runs when a session ends.

    Actions:
    1. Check if note creation criteria are met
    2. Summarize session progress
    3. Suggest next steps
    """

    def __init__(self):
        self.trigger_tools: set[str] = set()  # Triggered manually, not by tools

    async def should_execute(self, tool_name: str, tool_result: ToolResult) -> bool:
        # Session end hook is triggered manually by the agent loop
        return False

    async def execute(
        self,
        db: Database,
        user_id: str,
        tool_result: ToolResult | None = None,
        session_data: dict[str, Any] | None = None,
    ) -> HookResult:
        """Execute session end hooks.

        Args:
            db: Database connection
            user_id: User ID
            tool_result: Optional tool result (may be None for session end)
            session_data: Session metadata including progress changes
        """
        session_data = session_data or {}
        actions = []

        pattern_id = session_data.get("current_pattern")
        start_progress = session_data.get("start_progress", 0)
        current_progress = session_data.get("current_progress", 0)
        message_count = session_data.get("message_count", 0)

        progress_gain = current_progress - start_progress

        # Check note creation criteria
        if pattern_id and (progress_gain >= 20 or message_count >= 15):
            should_create, reason = should_create_note(
                pattern_id, current_progress, message_count, progress_gain
            )
            if should_create:
                actions.append(f"Note creation suggested: {reason}")

        # Session summary
        if progress_gain > 0:
            actions.append(f"Progress increased by {progress_gain}%")

        if message_count > 0:
            actions.append(f"Session had {message_count} messages")

        return HookResult(
            executed=True,
            action_taken="; ".join(actions) if actions else "Session ended",
            data={
                "pattern_id": pattern_id,
                "progress_gain": progress_gain,
                "message_count": message_count,
                "actions": actions,
            },
        )


class HookRegistry:
    """Registry for managing and executing hooks."""

    def __init__(self):
        self._hooks: list[Hook] = []

    def register(self, hook: Hook) -> None:
        """Register a hook."""
        self._hooks.append(hook)

    def register_defaults(self) -> None:
        """Register the default set of hooks."""
        self.register(QuestCompletionHook())
        self.register(LearningHook())
        self.register(SessionEndHook())

    async def execute_hooks(
        self, db: Database, user_id: str, tool_name: str, tool_result: ToolResult
    ) -> list[HookResult]:
        """Execute all applicable hooks for a tool result."""
        results = []

        for hook in self._hooks:
            if await hook.should_execute(tool_name, tool_result):
                result = await hook.execute(db, user_id, tool_result)
                results.append(result)

        return results

    async def execute_session_end(
        self, db: Database, user_id: str, session_data: dict[str, Any]
    ) -> HookResult:
        """Execute session end hook."""
        for hook in self._hooks:
            if isinstance(hook, SessionEndHook):
                return await hook.execute(db, user_id, None, session_data)

        return HookResult(executed=False, action_taken="No session end hook registered")


# Convenience function to create a pre-configured hook registry
def create_default_hook_registry() -> HookRegistry:
    """Create a hook registry with default hooks."""
    registry = HookRegistry()
    registry.register_defaults()
    return registry
