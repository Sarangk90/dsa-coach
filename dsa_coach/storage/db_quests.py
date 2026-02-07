"""Quest completion database operations mixin."""

from __future__ import annotations

from datetime import datetime

import aiosqlite

from .models import QuestCompletion


class QuestMixin:
    """Mixin providing quest completion CRUD operations."""

    conn: aiosqlite.Connection

    async def get_quest_completion(
        self, user_id: str, quest_id: str
    ) -> QuestCompletion | None:
        """Get completion record for a quest."""
        async with self.conn.execute(
            "SELECT * FROM quest_completions WHERE user_id = ? AND quest_id = ?",
            (user_id, quest_id),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_quest_completion(row)
            return None

    async def get_completed_quests(
        self, user_id: str = "default", pattern_id: str | None = None
    ) -> list[QuestCompletion]:
        """Get all completed quests, optionally filtered by pattern."""
        query = "SELECT * FROM quest_completions WHERE user_id = ?"
        params: list = [user_id]
        if pattern_id:
            query += " AND pattern_id = ?"
            params.append(pattern_id)
        query += " ORDER BY completed_at DESC"

        completions = []
        async with self.conn.execute(query, params) as cursor:
            async for row in cursor:
                completions.append(self._row_to_quest_completion(row))
        return completions

    async def get_due_reviews(self, user_id: str = "default") -> list[QuestCompletion]:
        """Get quests due for spaced repetition review.

        Includes both:
        - Previously reviewed quests where next review date has passed
        - First-time reviews (never reviewed, but completion date + interval has passed)
        """
        today = datetime.now().date().isoformat()
        completions = []
        async with self.conn.execute(
            """
            SELECT * FROM quest_completions
            WHERE user_id = ? AND (
                (last_reviewed IS NOT NULL
                 AND date(last_reviewed, '+' || next_review_in || ' days') <= date(?))
                OR
                (last_reviewed IS NULL
                 AND date(completed_at, '+' || next_review_in || ' days') <= date(?))
            )
            ORDER BY COALESCE(last_reviewed, completed_at)
            """,
            (user_id, today, today),
        ) as cursor:
            async for row in cursor:
                completions.append(self._row_to_quest_completion(row))
        return completions

    async def upsert_quest_completion(self, completion: QuestCompletion) -> None:
        """Create or update quest completion."""
        completion.id = f"{completion.user_id}_{completion.quest_id}"
        await self.conn.execute(
            """
            INSERT INTO quest_completions (id, user_id, quest_id, pattern_id, completed_at, time_minutes, hints_used, success, review_count, last_reviewed, next_review_in)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, quest_id) DO UPDATE SET
                completed_at = excluded.completed_at,
                time_minutes = excluded.time_minutes,
                hints_used = excluded.hints_used,
                success = excluded.success,
                review_count = excluded.review_count,
                last_reviewed = excluded.last_reviewed,
                next_review_in = excluded.next_review_in
            """,
            (
                completion.id,
                completion.user_id,
                completion.quest_id,
                completion.pattern_id,
                completion.completed_at.isoformat(),
                completion.time_minutes,
                completion.hints_used,
                1 if completion.success else 0,
                completion.review_count,
                completion.last_reviewed.isoformat()
                if completion.last_reviewed
                else None,
                completion.next_review_in,
            ),
        )
        await self.conn.commit()

    def _row_to_quest_completion(self, row: aiosqlite.Row) -> QuestCompletion:
        """Convert database row to QuestCompletion model."""
        return QuestCompletion(
            id=row["id"],
            user_id=row["user_id"],
            quest_id=row["quest_id"],
            pattern_id=row["pattern_id"],
            completed_at=datetime.fromisoformat(row["completed_at"]),
            time_minutes=row["time_minutes"],
            hints_used=row["hints_used"],
            success=bool(row["success"]),
            review_count=row["review_count"],
            last_reviewed=datetime.fromisoformat(row["last_reviewed"])
            if row["last_reviewed"]
            else None,
            next_review_in=row["next_review_in"],
        )
