"""Pattern progress and derived stats database operations mixin."""

from __future__ import annotations

import json
from datetime import datetime

import aiosqlite

from ..constants import (
    MASTERY_THRESHOLD,
    MAX_PROGRESS,
    POINTS_NO_HINTS,
    POINTS_WITH_HINTS,
)
from .models import PatternProgress


class ProgressMixin:
    """Mixin providing pattern progress and derived stats operations."""

    conn: aiosqlite.Connection

    async def get_pattern_progress(
        self, user_id: str, pattern_id: str
    ) -> PatternProgress | None:
        """Get progress for a specific pattern."""
        async with self.conn.execute(
            "SELECT * FROM pattern_progress WHERE user_id = ? AND pattern_id = ?",
            (user_id, pattern_id),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_pattern_progress(row)
            return None

    async def get_all_pattern_progress(
        self, user_id: str = "default"
    ) -> list[PatternProgress]:
        """Get progress for all patterns for a user."""
        progress_list = []
        async with self.conn.execute(
            "SELECT * FROM pattern_progress WHERE user_id = ? ORDER BY progress",
            (user_id,),
        ) as cursor:
            async for row in cursor:
                progress_list.append(self._row_to_pattern_progress(row))
        return progress_list

    async def upsert_pattern_progress(self, progress: PatternProgress) -> None:
        """Create or update pattern progress."""
        progress.id = f"{progress.user_id}_{progress.pattern_id}"
        await self.conn.execute(
            """
            INSERT INTO pattern_progress (id, user_id, pattern_id, progress, quests_completed, quests_total, concepts_understood, concepts_total, last_practiced, next_review, mastered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, pattern_id) DO UPDATE SET
                progress = excluded.progress,
                quests_completed = excluded.quests_completed,
                quests_total = excluded.quests_total,
                concepts_understood = excluded.concepts_understood,
                concepts_total = excluded.concepts_total,
                last_practiced = excluded.last_practiced,
                next_review = excluded.next_review,
                mastered = excluded.mastered
            """,
            (
                progress.id,
                progress.user_id,
                progress.pattern_id,
                progress.progress,
                progress.quests_completed,
                progress.quests_total,
                json.dumps(progress.concepts_understood),
                progress.concepts_total,
                progress.last_practiced.isoformat()
                if progress.last_practiced
                else None,
                progress.next_review.isoformat() if progress.next_review else None,
                1 if progress.mastered else 0,
            ),
        )
        await self.conn.commit()

    def _row_to_pattern_progress(self, row: aiosqlite.Row) -> PatternProgress:
        """Convert database row to PatternProgress model."""
        # Handle both old "confidence" column and new "progress" column for migration
        row_keys = row.keys()
        if "progress" in row_keys:
            progress_value = row["progress"]
        elif "confidence" in row_keys:
            progress_value = row["confidence"]
        else:
            progress_value = 0
        return PatternProgress(
            id=row["id"],
            user_id=row["user_id"],
            pattern_id=row["pattern_id"],
            progress=progress_value,
            quests_completed=row["quests_completed"],
            quests_total=row["quests_total"],
            concepts_understood=json.loads(row["concepts_understood"]),
            concepts_total=row["concepts_total"],
            last_practiced=datetime.fromisoformat(row["last_practiced"])
            if row["last_practiced"]
            else None,
            next_review=datetime.fromisoformat(row["next_review"])
            if row["next_review"]
            else None,
            mastered=bool(row["mastered"]),
        )

    # ==================== Derived Stats (Single Source of Truth) ====================

    async def get_derived_pattern_stats(
        self, user_id: str, pattern_id: str, quests_total: int | None = None
    ) -> dict[str, int | bool]:
        """Compute pattern stats from quest_completions table (source of truth).

        This replaces cached counters with live queries to prevent data drift.

        Progress formula: (earned_points / max_points) * 100
        where max_points = quests_total * 15 (points for completing all with no hints)

        Args:
            user_id: User identifier
            pattern_id: Pattern identifier
            quests_total: Total quests in pattern (for scaled progress).
                          If not provided, falls back to pattern_progress.quests_total.

        Returns: {"quests_completed": int, "progress": int, "mastered": bool}
        """
        async with self.conn.execute(
            """
            SELECT
                COUNT(*) as quests_completed,
                COALESCE(SUM(
                    CASE WHEN success = 1 THEN
                        CASE WHEN hints_used = 0 THEN ? ELSE ? END
                    ELSE 0 END
                ), 0) as earned_points
            FROM quest_completions
            WHERE user_id = ? AND pattern_id = ?
            """,
            (POINTS_NO_HINTS, POINTS_WITH_HINTS, user_id, pattern_id),
        ) as cursor:
            row = await cursor.fetchone()
            quests_completed = row[0] if row else 0
            earned_points = row[1] if row else 0

        # Fallback: get quests_total from pattern_progress if not provided
        if quests_total is None or quests_total == 0:
            async with self.conn.execute(
                "SELECT quests_total FROM pattern_progress WHERE user_id = ? AND pattern_id = ?",
                (user_id, pattern_id),
            ) as cursor:
                pp_row = await cursor.fetchone()
                if pp_row and pp_row[0]:
                    quests_total = pp_row[0]

        # Calculate scaled progress
        if quests_total and quests_total > 0:
            max_points = quests_total * POINTS_NO_HINTS
            progress = min(MAX_PROGRESS, round((earned_points / max_points) * 100))
        else:
            # If quests_total is unknown, use points directly and cap at 100.
            progress = min(MAX_PROGRESS, earned_points)

        return {
            "quests_completed": quests_completed,
            "progress": progress,
            "mastered": progress >= MASTERY_THRESHOLD,
        }

    async def get_total_quests_completed(self, user_id: str = "default") -> int:
        """Count total completed quests from records (source of truth)."""
        async with self.conn.execute(
            "SELECT COUNT(*) FROM quest_completions WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_derived_daily_stats(
        self, user_id: str, date_str: str
    ) -> dict[str, int | list[str]]:
        """Compute daily stats from quest_completions (source of truth).

        Returns: {"problems_solved": int, "time_spent_mins": int, "hints_used": int, "patterns_worked": list}
        """
        async with self.conn.execute(
            """
            SELECT
                COUNT(*) as problems_solved,
                COALESCE(SUM(time_minutes), 0) as time_spent_mins,
                COALESCE(SUM(hints_used), 0) as hints_used
            FROM quest_completions
            WHERE user_id = ? AND DATE(completed_at) = ?
            """,
            (user_id, date_str),
        ) as cursor:
            row = await cursor.fetchone()
            problems = row[0] if row else 0
            time_mins = row[1] if row else 0
            hints = row[2] if row else 0

        # Get unique patterns worked that day
        async with self.conn.execute(
            """
            SELECT DISTINCT pattern_id FROM quest_completions
            WHERE user_id = ? AND DATE(completed_at) = ?
            """,
            (user_id, date_str),
        ) as cursor:
            patterns = [row[0] async for row in cursor]

        return {
            "problems_solved": problems,
            "time_spent_mins": time_mins,
            "hints_used": hints,
            "patterns_worked": patterns,
        }
