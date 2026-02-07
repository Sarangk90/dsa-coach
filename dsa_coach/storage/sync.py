"""Synchronous wrapper for async Database operations.

This module provides a SyncDatabase class that wraps the async Database
for use in synchronous CLI commands.

Usage:
    with SyncDatabase() as db:
        profile = db.get_or_create_profile()
        due_reviews = db.get_due_reviews()
"""

import asyncio
from pathlib import Path

from .db import DEFAULT_DB_PATH, Database
from .models import (
    ConceptUnderstanding,
    PatternProgress,
    QuestCompletion,
    Session,
    UserProfile,
)


class SyncDatabase:
    """Synchronous wrapper around async Database.

    Wraps all async methods with asyncio.run() for use in sync contexts.
    Use as a context manager to ensure proper connection handling.
    """

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self._db = Database(db_path)
        self._connected = False

    def __enter__(self) -> "SyncDatabase":
        """Connect to database on context entry."""
        asyncio.run(self._db.connect())
        self._connected = True
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb) -> None:
        """Close database on context exit."""
        if self._connected:
            asyncio.run(self._db.close())
            self._connected = False

    def _run(self, coro):
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)

    # ==================== Profile Operations ====================

    def get_or_create_profile(self, user_id: str = "default") -> UserProfile:
        """Get user profile, creating if it doesn't exist."""
        return self._run(self._db.get_or_create_profile(user_id))

    def update_profile(self, profile: UserProfile) -> None:
        """Update user profile."""
        self._run(self._db.update_profile(profile))

    # ==================== Session Operations ====================

    def get_latest_session(self, user_id: str = "default") -> Session | None:
        """Get the most recent session for a user."""
        return self._run(self._db.get_latest_session(user_id))

    def create_session(
        self,
        user_id: str = "default",
        session_type: str = "general",
        current_pattern: str | None = None,
        current_quest: str | None = None,
    ) -> Session:
        """Create a new coaching session."""
        return self._run(
            self._db.create_session(
                user_id, session_type, current_pattern, current_quest
            )
        )

    def update_session(self, session: Session) -> None:
        """Update a session."""
        self._run(self._db.update_session(session))

    # ==================== Pattern Progress Operations ====================

    def get_pattern_progress(
        self, user_id: str, pattern_id: str
    ) -> PatternProgress | None:
        """Get progress for a specific pattern."""
        return self._run(self._db.get_pattern_progress(user_id, pattern_id))

    def get_all_pattern_progress(
        self, user_id: str = "default"
    ) -> list[PatternProgress]:
        """Get progress for all patterns for a user."""
        return self._run(self._db.get_all_pattern_progress(user_id))

    def upsert_pattern_progress(self, progress: PatternProgress) -> None:
        """Create or update pattern progress."""
        self._run(self._db.upsert_pattern_progress(progress))

    # ==================== Derived Stats (Single Source of Truth) ====================

    def get_derived_pattern_stats(
        self, user_id: str, pattern_id: str, quests_total: int | None = None
    ) -> dict[str, int | bool]:
        """Compute pattern stats from quest_completions table (source of truth)."""
        return self._run(
            self._db.get_derived_pattern_stats(user_id, pattern_id, quests_total)
        )

    def get_total_quests_completed(self, user_id: str = "default") -> int:
        """Count total completed quests from records (source of truth)."""
        return self._run(self._db.get_total_quests_completed(user_id))

    def get_derived_daily_stats(
        self, user_id: str, date_str: str
    ) -> dict[str, int | list[str]]:
        """Compute daily stats from quest_completions (source of truth)."""
        return self._run(self._db.get_derived_daily_stats(user_id, date_str))

    # ==================== Quest Completion Operations ====================

    def get_quest_completion(
        self, user_id: str, quest_id: str
    ) -> QuestCompletion | None:
        """Get completion record for a quest."""
        return self._run(self._db.get_quest_completion(user_id, quest_id))

    def get_completed_quests(
        self, user_id: str = "default", pattern_id: str | None = None
    ) -> list[QuestCompletion]:
        """Get all completed quests, optionally filtered by pattern."""
        return self._run(self._db.get_completed_quests(user_id, pattern_id))

    def get_due_reviews(self, user_id: str = "default") -> list[QuestCompletion]:
        """Get quests due for spaced repetition review."""
        return self._run(self._db.get_due_reviews(user_id))

    def upsert_quest_completion(self, completion: QuestCompletion) -> None:
        """Create or update quest completion."""
        self._run(self._db.upsert_quest_completion(completion))

    # ==================== Concept Understanding Operations ====================

    def get_concept_understanding(
        self, user_id: str, pattern_id: str, concept: str
    ) -> ConceptUnderstanding | None:
        """Get understanding record for a specific concept."""
        return self._run(
            self._db.get_concept_understanding(user_id, pattern_id, concept)
        )

    def get_pattern_concepts(
        self, user_id: str, pattern_id: str
    ) -> list[ConceptUnderstanding]:
        """Get all concept understanding records for a pattern."""
        return self._run(self._db.get_pattern_concepts(user_id, pattern_id))

    def upsert_concept_understanding(self, concept: ConceptUnderstanding) -> None:
        """Create or update concept understanding."""
        self._run(self._db.upsert_concept_understanding(concept))

    # ==================== Mistakes Operations ====================

    def add_mistake(
        self,
        user_id: str,
        quest_id: str,
        pattern_id: str,
        mistake_type: str,
        description: str,
        lesson_learned: str | None = None,
    ) -> str:
        """Add a mistake, incrementing recurrence if same type exists for pattern."""
        return self._run(
            self._db.add_mistake(
                user_id, quest_id, pattern_id, mistake_type, description, lesson_learned
            )
        )

    def get_recent_mistakes(self, user_id: str, limit: int = 5) -> list[dict]:
        """Get most recent mistakes."""
        return self._run(self._db.get_recent_mistakes(user_id, limit))

    def get_recurring_mistake_types(self, user_id: str) -> list[dict]:
        """Get mistake types that occur 2+ times."""
        return self._run(self._db.get_recurring_mistake_types(user_id))

    # ==================== Daily Logs Operations ====================

    def upsert_daily_log(
        self,
        user_id: str,
        problems_delta: int = 0,
        time_delta_mins: int = 0,
        hints_delta: int = 0,
        pattern_worked: str | None = None,
    ) -> None:
        """Update or create today's daily log."""
        self._run(
            self._db.upsert_daily_log(
                user_id, problems_delta, time_delta_mins, hints_delta, pattern_worked
            )
        )

    def get_weekly_activity(self, user_id: str) -> dict:
        """Get activity summary for current week."""
        return self._run(self._db.get_weekly_activity(user_id))

    # ==================== Milestones Operations ====================

    def add_milestone(
        self,
        user_id: str,
        milestone_type: str,
        description: str,
        pattern_id: str | None = None,
        quest_id: str | None = None,
    ) -> str:
        """Add a milestone achievement."""
        return self._run(
            self._db.add_milestone(
                user_id, milestone_type, description, pattern_id, quest_id
            )
        )

    def get_recent_milestones(self, user_id: str, days: int = 7) -> list[dict]:
        """Get milestones achieved in last N days."""
        return self._run(self._db.get_recent_milestones(user_id, days))

    # ==================== Teaching History Operations ====================

    def record_teaching(
        self,
        user_id: str,
        pattern_id: str,
        concept: str,
        student_response: str = "unknown",
    ) -> None:
        """Record that a concept was taught, incrementing count if exists."""
        self._run(
            self._db.record_teaching(user_id, pattern_id, concept, student_response)
        )

    def get_teaching_history(
        self, user_id: str, pattern_id: str | None = None
    ) -> list[dict]:
        """Get teaching history, optionally filtered by pattern."""
        return self._run(self._db.get_teaching_history(user_id, pattern_id))

    # ==================== Student Context Query Methods ====================

    def get_struggling_concepts(self, user_id: str) -> list[dict]:
        """Get concepts where student is struggling."""
        return self._run(self._db.get_struggling_concepts(user_id))

    def get_mastered_concepts(self, user_id: str) -> list[dict]:
        """Get concepts that student has mastered."""
        return self._run(self._db.get_mastered_concepts(user_id))
