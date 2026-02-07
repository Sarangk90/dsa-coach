"""
CoachTestHarness - Programmatic test harness for DSA Coach agent.

This harness allows automated testing of the coach agent with:
- Conversation management (send messages, get responses)
- State inspection (verify database changes after tool calls)
- Snapshot/diff capabilities (see what changed)
- Assertion helpers for common checks

Usage:
    async with CoachTestHarness() as harness:
        # Have a conversation
        response = await harness.send("What should I work on next?")
        print(response.content)
        print(response.tools_used)

        # Inspect state after agent actions
        patterns = await harness.inspect_patterns()
        mistakes = await harness.inspect_mistakes()

        # Take snapshots to see what changed
        before = await harness.snapshot()
        await harness.send("I completed the sliding window problem")
        after = await harness.snapshot()
        diff = harness.diff_snapshot(before, after)
"""

from __future__ import annotations

import asyncio
import json
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from dsa_coach.agent.sdk_agent import SDKCoachAgent
from dsa_coach.storage.db import Database
from dsa_coach.storage.models import (
    ConceptUnderstanding,
    PatternProgress,
    QuestCompletion,
    UserProfile,
)


@dataclass
class ConversationResponse:
    """Structured response from the agent."""

    content: str
    tools_used: list[str] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)
    state_updated: bool = False
    error: str | None = None
    raw_response: Any = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "content": self.content,
            "tools_used": self.tools_used,
            "tool_results": self.tool_results,
            "state_updated": self.state_updated,
            "error": self.error,
        }


@dataclass
class DatabaseSnapshot:
    """Snapshot of database state for comparison."""

    timestamp: datetime
    profile: UserProfile | None
    patterns: list[PatternProgress]
    quests: list[QuestCompletion]
    mistakes: list[dict]  # Database returns dicts
    milestones: list[dict]  # Database returns dicts
    teaching_history: list[dict]  # Database returns dicts
    concepts: list[ConceptUnderstanding]
    current_session: dict | None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "profile": self.profile.model_dump() if self.profile else None,
            "patterns": [p.model_dump() for p in self.patterns],
            "quests": [q.model_dump() for q in self.quests],
            "mistakes": self.mistakes,  # Already dicts
            "milestones": self.milestones,  # Already dicts
            "teaching_history": self.teaching_history,  # Already dicts
            "concepts": [c.model_dump() for c in self.concepts],
            "current_session": self.current_session,
        }


class CoachTestHarness:
    """
    Test harness for DSA Coach agent.

    Provides programmatic control over the agent with:
    - Isolated test database (temporary file)
    - Conversation management
    - State inspection and verification
    - Snapshot/diff capabilities

    Example:
        async with CoachTestHarness() as harness:
            await harness.hydrate_test_data()
            response = await harness.send("Show me my progress")
            assert "pattern" in response.content.lower()
    """

    def __init__(
        self,
        db_path: Path | None = None,
        user_id: str = "test_user",
        auto_hydrate: bool = False,
    ):
        """
        Initialize the test harness.

        Args:
            db_path: Path to test database. If None, uses a temp file.
            user_id: User ID for test data isolation.
            auto_hydrate: If True, automatically populate with test data.
        """
        self._temp_dir: tempfile.TemporaryDirectory | None = None
        self._db_path = db_path
        self._user_id = user_id
        self._auto_hydrate = auto_hydrate

        self.db: Database | None = None
        self.agent: SDKCoachAgent | None = None
        self._conversation_history: list[dict] = []

    async def __aenter__(self) -> CoachTestHarness:
        """Async context manager entry."""
        await self.setup()
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb) -> None:
        """Async context manager exit."""
        await self.cleanup()

    @property
    def db_path(self) -> Path:
        """Get the database path."""
        if self._db_path:
            return self._db_path
        if self._temp_dir:
            return Path(self._temp_dir.name) / "test_coach.db"
        raise RuntimeError("Harness not initialized")

    async def setup(self) -> None:
        """Initialize the harness, database, and agent."""
        # Create temp directory if no db_path specified
        if not self._db_path:
            self._temp_dir = tempfile.TemporaryDirectory(prefix="dsa_coach_test_")

        # Initialize database
        self.db = Database(self.db_path)
        await self.db.connect()

        # Optionally hydrate with test data
        if self._auto_hydrate:
            await self.hydrate_test_data()

        # Initialize agent
        self.agent = SDKCoachAgent(self.db, user_id=self._user_id)
        await self.agent.initialize()

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.db:
            await self.db.close()
        if self._temp_dir:
            self._temp_dir.cleanup()

    # =========================================================================
    # CONVERSATION METHODS
    # =========================================================================

    async def send(self, message: str) -> ConversationResponse:
        """
        Send a message to the agent and get a response.

        Args:
            message: The user message to send.

        Returns:
            ConversationResponse with content, tools used, and state changes.
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call setup() first.")

        # Track reasoning/intermediate text
        reasoning_parts: list[str] = []

        def on_reasoning(text: str) -> None:
            reasoning_parts.append(text)

        # Send to agent
        response = await self.agent.run(message, on_reasoning=on_reasoning)

        # Build structured response
        result = ConversationResponse(
            content=response.content,
            tools_used=[tc["name"] for tc in response.tool_calls_made],
            tool_results=[
                {"name": tc["name"], "args": tc["args"]}
                for tc in response.tool_calls_made
            ],
            state_updated=response.state_updated,
            error=response.error,
            raw_response=response,
        )

        # Track conversation
        self._conversation_history.append(
            {
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._conversation_history.append(
            {
                "role": "assistant",
                "content": result.content,
                "tools": result.tools_used,
                "timestamp": datetime.now().isoformat(),
            }
        )

        return result

    async def get_greeting(self) -> str:
        """Get the agent's greeting message."""
        if not self.agent:
            raise RuntimeError("Agent not initialized")
        return await self.agent.get_greeting()

    def get_conversation_history(self) -> list[dict]:
        """Get the full conversation history."""
        return self._conversation_history.copy()

    def clear_conversation(self) -> None:
        """Clear conversation history (but keep database state)."""
        self._conversation_history.clear()
        # Note: This doesn't reset the agent's session

    # =========================================================================
    # STATE INSPECTION METHODS
    # =========================================================================

    async def inspect_profile(self) -> UserProfile:
        """Get the current user profile."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.get_or_create_profile(self._user_id)

    async def inspect_patterns(self) -> list[PatternProgress]:
        """Get all pattern progress records."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.get_all_pattern_progress(self._user_id)

    async def inspect_pattern(self, pattern_id: str) -> PatternProgress | None:
        """Get progress for a specific pattern."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.get_pattern_progress(self._user_id, pattern_id)

    async def inspect_quests(self) -> list[QuestCompletion]:
        """Get all completed quests."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.get_completed_quests(self._user_id)

    async def inspect_quest(self, quest_id: str) -> QuestCompletion | None:
        """Check if a specific quest is completed."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        quests = await self.db.get_completed_quests(self._user_id)
        return next((q for q in quests if q.quest_id == quest_id), None)

    async def inspect_due_reviews(self) -> list[QuestCompletion]:
        """Get quests due for review."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.get_due_reviews(self._user_id)

    async def inspect_mistakes(self) -> list[dict]:
        """Get all recorded mistakes."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.get_recent_mistakes(self._user_id, limit=100)

    async def inspect_recurring_mistakes(self) -> list[dict]:
        """Get recurring mistake types."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.get_recurring_mistake_types(self._user_id)

    async def inspect_milestones(self) -> list[dict]:
        """Get all milestones."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.get_recent_milestones(self._user_id, days=365)

    async def inspect_teaching_history(self) -> list[dict]:
        """Get teaching history."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.get_teaching_history(self._user_id)

    async def inspect_concepts(
        self, pattern_id: str | None = None
    ) -> list[ConceptUnderstanding]:
        """Get concept understanding records for a pattern."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        # If pattern_id is provided, get concepts for that pattern
        # Otherwise, get all concepts by iterating through known patterns
        if pattern_id:
            return await self.db.get_pattern_concepts(self._user_id, pattern_id)

        # Get all pattern progress to find patterns with concepts
        all_concepts: list[ConceptUnderstanding] = []
        patterns = await self.db.get_all_pattern_progress(self._user_id)
        for pattern in patterns:
            concepts = await self.db.get_pattern_concepts(
                self._user_id, pattern.pattern_id
            )
            all_concepts.extend(concepts)
        return all_concepts

    async def inspect_current_session(self) -> dict | None:
        """Get the current session info."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        session = await self.db.get_latest_session(self._user_id)
        if session:
            return session.model_dump()
        return None

    async def inspect_weekly_activity(self) -> dict:
        """Get weekly activity summary."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        return await self.db.get_weekly_activity(self._user_id)

    # =========================================================================
    # SNAPSHOT AND DIFF METHODS
    # =========================================================================

    async def snapshot(self) -> DatabaseSnapshot:
        """
        Take a complete snapshot of the database state.

        Useful for comparing before/after states.
        """
        if not self.db:
            raise RuntimeError("Database not initialized")

        profile = await self.db.get_or_create_profile(self._user_id)
        patterns = await self.db.get_all_pattern_progress(self._user_id)
        quests = await self.db.get_completed_quests(self._user_id)
        mistakes = await self.db.get_recent_mistakes(self._user_id, limit=100)
        milestones = await self.db.get_recent_milestones(self._user_id, days=365)
        teaching = await self.db.get_teaching_history(self._user_id)
        session = await self.db.get_latest_session(self._user_id)

        # Get all concepts by iterating through patterns
        all_concepts: list[ConceptUnderstanding] = []
        for pattern in patterns:
            concepts = await self.db.get_pattern_concepts(
                self._user_id, pattern.pattern_id
            )
            all_concepts.extend(concepts)

        return DatabaseSnapshot(
            timestamp=datetime.now(),
            profile=profile,
            patterns=patterns,
            quests=quests,
            mistakes=mistakes,
            milestones=milestones,
            teaching_history=teaching,
            concepts=all_concepts,
            current_session=session.model_dump() if session else None,
        )

    def diff_snapshot(
        self, before: DatabaseSnapshot, after: DatabaseSnapshot
    ) -> dict[str, Any]:
        """
        Compare two snapshots and return the differences.

        Returns a dict with keys for each entity type that changed.
        """
        diff: dict[str, Any] = {}

        # Profile changes
        if before.profile and after.profile:
            profile_changes = {}
            for field in ["quests_completed", "name", "last_active"]:
                before_val = getattr(before.profile, field, None)
                after_val = getattr(after.profile, field, None)
                if before_val != after_val:
                    profile_changes[field] = {"before": before_val, "after": after_val}
            if profile_changes:
                diff["profile"] = profile_changes

        # Pattern progress changes
        before_patterns = {p.pattern_id: p for p in before.patterns}
        after_patterns = {p.pattern_id: p for p in after.patterns}

        pattern_changes: dict[str, Any] = {}
        for pid in set(before_patterns) | set(after_patterns):
            bp = before_patterns.get(pid)
            ap = after_patterns.get(pid)

            if bp is None and ap is not None:
                pattern_changes[pid] = {"added": True, "progress": ap.progress}
            elif bp is not None and ap is None:
                pattern_changes[pid] = {"removed": True}
            elif bp and ap:
                changes = {}
                for field in ["progress", "quests_completed", "mastered"]:
                    bv = getattr(bp, field)
                    av = getattr(ap, field)
                    if bv != av:
                        changes[field] = {"before": bv, "after": av}
                if changes:
                    pattern_changes[pid] = changes

        if pattern_changes:
            diff["patterns"] = pattern_changes

        # Quest completions changes
        before_quests = {q.quest_id for q in before.quests}
        after_quests = {q.quest_id for q in after.quests}

        new_quests = after_quests - before_quests
        if new_quests:
            diff["quests_added"] = list(new_quests)

        # Mistakes changes
        before_mistakes = len(before.mistakes)
        after_mistakes = len(after.mistakes)
        if after_mistakes > before_mistakes:
            new_count = after_mistakes - before_mistakes
            new_mistakes = after.mistakes[:new_count]
            diff["mistakes_added"] = [
                {"type": m["mistake_type"], "description": m["description"]}
                for m in new_mistakes
            ]

        # Milestones changes
        before_milestones = len(before.milestones)
        after_milestones = len(after.milestones)
        if after_milestones > before_milestones:
            new_count = after_milestones - before_milestones
            new_milestones = after.milestones[:new_count]
            diff["milestones_added"] = [
                # DB returns "type" not "milestone_type" from get_recent_milestones
                {
                    "type": m.get("type", m.get("milestone_type")),
                    "description": m["description"],
                }
                for m in new_milestones
            ]

        return diff

    # =========================================================================
    # ASSERTION HELPERS
    # =========================================================================

    async def assert_pattern_progress(
        self, pattern_id: str, expected: int, tolerance: int = 5
    ) -> None:
        """Assert that a pattern has the expected progress level."""
        pattern = await self.inspect_pattern(pattern_id)
        if not pattern:
            raise AssertionError(f"Pattern '{pattern_id}' not found")

        if abs(pattern.progress - expected) > tolerance:
            raise AssertionError(
                f"Pattern '{pattern_id}' progress is {pattern.progress}, "
                f"expected {expected} (±{tolerance})"
            )

    async def assert_quest_completed(self, quest_id: str) -> None:
        """Assert that a quest has been completed."""
        quest = await self.inspect_quest(quest_id)
        if not quest:
            raise AssertionError(f"Quest '{quest_id}' is not completed")

    async def assert_mistake_recorded(self, mistake_type: str) -> None:
        """Assert that a mistake of the given type was recorded."""
        mistakes = await self.inspect_mistakes()
        types = [m["mistake_type"] for m in mistakes]
        if mistake_type not in types:
            raise AssertionError(
                f"Mistake type '{mistake_type}' not found. Recorded types: {types}"
            )

    async def assert_milestone_achieved(self, milestone_type: str) -> None:
        """Assert that a milestone of the given type was achieved."""
        milestones = await self.inspect_milestones()
        # DB returns "type" not "milestone_type" from get_recent_milestones
        types = [m.get("type", m.get("milestone_type")) for m in milestones]
        if milestone_type not in types:
            raise AssertionError(
                f"Milestone type '{milestone_type}' not found. Achieved types: {types}"
            )

    async def assert_tool_was_used(
        self, response: ConversationResponse, tool_name: str
    ) -> None:
        """Assert that a specific tool was used in the response."""
        if tool_name not in response.tools_used:
            raise AssertionError(
                f"Tool '{tool_name}' was not used. Tools used: {response.tools_used}"
            )

    async def assert_content_contains(
        self, response: ConversationResponse, text: str, case_sensitive: bool = False
    ) -> None:
        """Assert that the response content contains the given text."""
        content = response.content
        search_text = text

        if not case_sensitive:
            content = content.lower()
            search_text = text.lower()

        if search_text not in content:
            raise AssertionError(
                f"Response does not contain '{text}'. "
                f"Response: {response.content[:200]}..."
            )

    # =========================================================================
    # TEST DATA HYDRATION
    # =========================================================================

    async def hydrate_test_data(self) -> None:
        """
        Populate the database with realistic test data.

        Creates a user profile with varied pattern progress, some completed
        quests, mistakes, and milestones for comprehensive testing.
        """
        if not self.db:
            raise RuntimeError("Database not initialized")

        from datetime import timedelta

        now = datetime.now()

        def days_ago(n: int) -> datetime:
            return now - timedelta(days=n)

        # Create user profile (get_or_create first, then update)
        profile = await self.db.get_or_create_profile(self._user_id)
        profile.name = "Test Student"
        profile.quests_completed = 5
        profile.created_at = days_ago(14)
        profile.last_active = now
        await self.db.update_profile(profile)

        # Create pattern progress with varying levels
        patterns_data = [
            ("arrays_hashing", 75, 4, 6, True),  # Arrays - mastered
            ("two_pointers", 50, 2, 5, False),  # Two Pointers - in progress
            ("sliding_window", 25, 1, 4, False),  # Sliding Window - started
            ("binary_search", 0, 0, 5, False),  # Binary Search - not started
        ]

        for pid, prog, completed, total, mastered in patterns_data:
            pp = PatternProgress(
                id=f"{self._user_id}_{pid}",
                user_id=self._user_id,
                pattern_id=pid,
                progress=prog,
                quests_completed=completed,
                quests_total=total,
                mastered=mastered,
                last_practiced=days_ago(2) if completed > 0 else None,
            )
            await self.db.upsert_pattern_progress(pp)

        # Create some quest completions
        quests_data = [
            ("arrays_hashing_two_sum", "arrays_hashing", days_ago(10), 25, 1),
            ("arrays_hashing_group_anagrams", "arrays_hashing", days_ago(8), 20, 0),
            (
                "arrays_hashing_subarray_sum_equals_k",
                "arrays_hashing",
                days_ago(6),
                30,
                2,
            ),
            ("two_pointers_3sum", "two_pointers", days_ago(4), 35, 1),
            (
                "sliding_window_longest_substring_without_repeating",
                "sliding_window",
                days_ago(2),
                45,
                2,
            ),
        ]

        for qid, pid, completed_at, time_mins, hints in quests_data:
            qc = QuestCompletion(
                id=f"{self._user_id}_{qid}",
                user_id=self._user_id,
                quest_id=qid,
                pattern_id=pid,
                completed_at=completed_at,
                time_minutes=time_mins,
                hints_used=hints,
            )
            await self.db.upsert_quest_completion(qc)

        # Create a mistake
        await self.db.add_mistake(
            user_id=self._user_id,
            quest_id="sliding_window_longest_substring_without_repeating",
            pattern_id="sliding_window",
            mistake_type="off_by_one",
            description="Window boundary was inclusive instead of exclusive",
            lesson_learned="Always clarify boundary conditions",
        )

        # Create a milestone
        await self.db.add_milestone(
            user_id=self._user_id,
            milestone_type="pattern_mastered",
            description="Mastered Arrays & Hashing pattern",
            pattern_id="arrays_hashing",
        )

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def to_json(self) -> str:
        """Export current state as JSON string."""
        return json.dumps(
            {
                "user_id": self._user_id,
                "db_path": str(self.db_path),
                "conversation_history": self._conversation_history,
            },
            indent=2,
            default=str,
        )


# =============================================================================
# SYNCHRONOUS WRAPPER (for CLI/script usage)
# =============================================================================


class SyncCoachTestHarness:
    """
    Synchronous wrapper around CoachTestHarness.

    Useful for scripts and CLI tools that don't want to deal with async.

    Example:
        with SyncCoachTestHarness() as harness:
            response = harness.send("Hello!")
            print(response.content)
    """

    def __init__(self, **kwargs):
        self._harness = CoachTestHarness(**kwargs)
        self._loop: asyncio.AbstractEventLoop | None = None

    def __enter__(self) -> SyncCoachTestHarness:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._harness.setup())
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb) -> None:
        if self._loop:
            self._loop.run_until_complete(self._harness.cleanup())
            self._loop.close()

    def _run(self, coro):
        """Run a coroutine synchronously."""
        if not self._loop:
            raise RuntimeError("Harness not initialized")
        return self._loop.run_until_complete(coro)

    def send(self, message: str) -> ConversationResponse:
        return self._run(self._harness.send(message))

    def get_greeting(self) -> str:
        return self._run(self._harness.get_greeting())

    def snapshot(self) -> DatabaseSnapshot:
        return self._run(self._harness.snapshot())

    def diff_snapshot(
        self, before: DatabaseSnapshot, after: DatabaseSnapshot
    ) -> dict[str, Any]:
        return self._harness.diff_snapshot(before, after)

    def hydrate_test_data(self) -> None:
        self._run(self._harness.hydrate_test_data())

    # Inspection methods
    def inspect_profile(self) -> UserProfile:
        return self._run(self._harness.inspect_profile())

    def inspect_patterns(self) -> list[PatternProgress]:
        return self._run(self._harness.inspect_patterns())

    def inspect_quests(self) -> list[QuestCompletion]:
        return self._run(self._harness.inspect_quests())

    def inspect_mistakes(self) -> list[dict]:
        return self._run(self._harness.inspect_mistakes())

    def inspect_milestones(self) -> list[dict]:
        return self._run(self._harness.inspect_milestones())

    def get_conversation_history(self) -> list[dict]:
        return self._harness.get_conversation_history()
