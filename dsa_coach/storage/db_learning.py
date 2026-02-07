"""Learning-related database operations mixin: concepts, mistakes, daily logs, milestones, teaching history."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import Any

import aiosqlite

from .models import ConceptUnderstanding


class LearningMixin:
    """Mixin providing concept understanding, mistakes, daily logs, milestones, and teaching history operations."""

    conn: aiosqlite.Connection

    # ==================== Concept Understanding Operations ====================

    async def get_concept_understanding(
        self, user_id: str, pattern_id: str, concept: str
    ) -> ConceptUnderstanding | None:
        """Get understanding record for a specific concept."""
        async with self.conn.execute(
            "SELECT * FROM concept_understanding WHERE user_id = ? AND pattern_id = ? AND concept = ?",
            (user_id, pattern_id, concept),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_concept_understanding(row)
            return None

    async def get_pattern_concepts(
        self, user_id: str, pattern_id: str
    ) -> list[ConceptUnderstanding]:
        """Get all concept understanding records for a pattern."""
        concepts = []
        async with self.conn.execute(
            "SELECT * FROM concept_understanding WHERE user_id = ? AND pattern_id = ?",
            (user_id, pattern_id),
        ) as cursor:
            async for row in cursor:
                concepts.append(self._row_to_concept_understanding(row))
        return concepts

    async def upsert_concept_understanding(self, concept: ConceptUnderstanding) -> None:
        """Create or update concept understanding."""
        concept.id = f"{concept.user_id}_{concept.pattern_id}_{concept.concept}"
        await self.conn.execute(
            """
            INSERT INTO concept_understanding (id, user_id, pattern_id, concept, understood, diagnosed_at, taught_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, pattern_id, concept) DO UPDATE SET
                understood = excluded.understood,
                diagnosed_at = excluded.diagnosed_at,
                taught_at = excluded.taught_at,
                notes = excluded.notes
            """,
            (
                concept.id,
                concept.user_id,
                concept.pattern_id,
                concept.concept,
                1 if concept.understood else 0,
                concept.diagnosed_at.isoformat() if concept.diagnosed_at else None,
                concept.taught_at.isoformat() if concept.taught_at else None,
                concept.notes,
            ),
        )
        await self.conn.commit()

    def _row_to_concept_understanding(self, row: aiosqlite.Row) -> ConceptUnderstanding:
        """Convert database row to ConceptUnderstanding model."""
        return ConceptUnderstanding(
            id=row["id"],
            user_id=row["user_id"],
            pattern_id=row["pattern_id"],
            concept=row["concept"],
            understood=bool(row["understood"]),
            diagnosed_at=datetime.fromisoformat(row["diagnosed_at"])
            if row["diagnosed_at"]
            else None,
            taught_at=datetime.fromisoformat(row["taught_at"])
            if row["taught_at"]
            else None,
            notes=row["notes"],
        )

    # ==================== Mistakes Operations ====================

    async def add_mistake(
        self,
        user_id: str,
        quest_id: str,
        pattern_id: str,
        mistake_type: str,
        description: str,
        lesson_learned: str | None = None,
    ) -> str:
        """Add a mistake, incrementing recurrence if same type exists for pattern."""
        # Check for existing mistake of same type for this pattern
        async with self.conn.execute(
            """
            SELECT id, recurrence_count FROM mistakes
            WHERE user_id = ? AND pattern_id = ? AND mistake_type = ?
            ORDER BY logged_at DESC LIMIT 1
            """,
            (user_id, pattern_id, mistake_type),
        ) as cursor:
            row = await cursor.fetchone()

        if row:
            # Increment recurrence count
            await self.conn.execute(
                "UPDATE mistakes SET recurrence_count = recurrence_count + 1 WHERE id = ?",
                (row["id"],),
            )
            await self.conn.commit()
            return str(row["id"])

        # Create new mistake
        mistake_id = str(uuid.uuid4())
        await self.conn.execute(
            """
            INSERT INTO mistakes (id, user_id, quest_id, pattern_id, mistake_type, description, lesson_learned, logged_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mistake_id,
                user_id,
                quest_id,
                pattern_id,
                mistake_type,
                description,
                lesson_learned,
                datetime.now().isoformat(),
            ),
        )
        await self.conn.commit()
        return mistake_id

    async def get_recent_mistakes(self, user_id: str, limit: int = 5) -> list[dict]:
        """Get most recent mistakes."""
        mistakes = []
        async with self.conn.execute(
            """
            SELECT * FROM mistakes WHERE user_id = ?
            ORDER BY logged_at DESC LIMIT ?
            """,
            (user_id, limit),
        ) as cursor:
            async for row in cursor:
                mistakes.append(
                    {
                        "id": row["id"],
                        "quest_id": row["quest_id"],
                        "pattern_id": row["pattern_id"],
                        "mistake_type": row["mistake_type"],
                        "description": row["description"],
                        "lesson_learned": row["lesson_learned"],
                        "logged_at": row["logged_at"],
                        "recurrence_count": row["recurrence_count"],
                    }
                )
        return mistakes

    async def get_recurring_mistake_types(self, user_id: str) -> list[dict]:
        """Get mistake types that occur 2+ times."""
        mistakes = []
        async with self.conn.execute(
            """
            SELECT mistake_type, SUM(recurrence_count) as total_count,
                   GROUP_CONCAT(DISTINCT pattern_id) as patterns
            FROM mistakes WHERE user_id = ?
            GROUP BY mistake_type
            HAVING total_count >= 2
            ORDER BY total_count DESC
            """,
            (user_id,),
        ) as cursor:
            async for row in cursor:
                mistakes.append(
                    {
                        "type": row["mistake_type"],
                        "count": row["total_count"],
                        "patterns": row["patterns"].split(",")
                        if row["patterns"]
                        else [],
                    }
                )
        return mistakes

    # ==================== Daily Logs Operations ====================

    async def upsert_daily_log(
        self,
        user_id: str,
        problems_delta: int = 0,
        time_delta_mins: int = 0,
        hints_delta: int = 0,
        pattern_worked: str | None = None,
    ) -> None:
        """Update or create today's daily log."""
        today = datetime.now().date().isoformat()
        log_id = f"{user_id}_{today}"

        # Get existing patterns
        async with self.conn.execute(
            "SELECT patterns_worked FROM daily_logs WHERE id = ?", (log_id,)
        ) as cursor:
            row = await cursor.fetchone()
            patterns = json.loads(row["patterns_worked"]) if row else []

        if pattern_worked and pattern_worked not in patterns:
            patterns.append(pattern_worked)

        await self.conn.execute(
            """
            INSERT INTO daily_logs (id, user_id, date, problems_solved, time_spent_mins, hints_used, patterns_worked)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET
                problems_solved = problems_solved + ?,
                time_spent_mins = time_spent_mins + ?,
                hints_used = hints_used + ?,
                patterns_worked = ?
            """,
            (
                log_id,
                user_id,
                today,
                problems_delta,
                time_delta_mins,
                hints_delta,
                json.dumps(patterns),
                problems_delta,
                time_delta_mins,
                hints_delta,
                json.dumps(patterns),
            ),
        )
        await self.conn.commit()

    async def get_weekly_activity(self, user_id: str) -> dict:
        """Get activity summary for current week."""
        week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()

        totals: dict[str, Any] = {
            "sessions": 0,
            "problems_solved": 0,
            "time_mins": 0,
            "patterns": set(),
        }

        async with self.conn.execute(
            """
            SELECT * FROM daily_logs
            WHERE user_id = ? AND date >= ?
            ORDER BY date
            """,
            (user_id, week_ago),
        ) as cursor:
            async for row in cursor:
                totals["sessions"] += 1
                totals["problems_solved"] += row["problems_solved"]
                totals["time_mins"] += row["time_spent_mins"]
                patterns = json.loads(row["patterns_worked"])
                totals["patterns"].update(patterns)

        totals["patterns"] = list(totals["patterns"])
        return totals

    # ==================== Milestones Operations ====================

    async def add_milestone(
        self,
        user_id: str,
        milestone_type: str,
        description: str,
        pattern_id: str | None = None,
        quest_id: str | None = None,
    ) -> str:
        """Add a milestone achievement."""
        milestone_id = str(uuid.uuid4())
        await self.conn.execute(
            """
            INSERT INTO milestones (id, user_id, milestone_type, pattern_id, quest_id, description, achieved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                milestone_id,
                user_id,
                milestone_type,
                pattern_id,
                quest_id,
                description,
                datetime.now().isoformat(),
            ),
        )
        await self.conn.commit()
        return milestone_id

    async def get_recent_milestones(self, user_id: str, days: int = 7) -> list[dict]:
        """Get milestones achieved in last N days."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        milestones = []
        async with self.conn.execute(
            """
            SELECT * FROM milestones
            WHERE user_id = ? AND achieved_at >= ?
            ORDER BY achieved_at DESC
            """,
            (user_id, cutoff),
        ) as cursor:
            async for row in cursor:
                milestones.append(
                    {
                        "id": row["id"],
                        "type": row["milestone_type"],
                        "pattern_id": row["pattern_id"],
                        "quest_id": row["quest_id"],
                        "description": row["description"],
                        "achieved_at": row["achieved_at"],
                    }
                )
        return milestones

    # ==================== Teaching History Operations ====================

    async def record_teaching(
        self,
        user_id: str,
        pattern_id: str,
        concept: str,
        student_response: str = "unknown",
    ) -> None:
        """Record that a concept was taught, incrementing count if exists."""
        record_id = f"{user_id}_{pattern_id}_{concept}"
        now = datetime.now().isoformat()

        await self.conn.execute(
            """
            INSERT INTO teaching_history (id, user_id, pattern_id, concept, explanation_count, last_explained, student_response)
            VALUES (?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(user_id, pattern_id, concept) DO UPDATE SET
                explanation_count = explanation_count + 1,
                last_explained = ?,
                student_response = ?
            """,
            (
                record_id,
                user_id,
                pattern_id,
                concept,
                now,
                student_response,
                now,
                student_response,
            ),
        )
        await self.conn.commit()

    async def get_teaching_history(
        self, user_id: str, pattern_id: str | None = None
    ) -> list[dict]:
        """Get teaching history, optionally filtered by pattern."""
        query = "SELECT * FROM teaching_history WHERE user_id = ?"
        params: list = [user_id]
        if pattern_id:
            query += " AND pattern_id = ?"
            params.append(pattern_id)
        query += " ORDER BY last_explained DESC"

        history = []
        async with self.conn.execute(query, params) as cursor:
            async for row in cursor:
                history.append(
                    {
                        "pattern_id": row["pattern_id"],
                        "concept": row["concept"],
                        "explanation_count": row["explanation_count"],
                        "last_explained": row["last_explained"],
                        "student_response": row["student_response"],
                    }
                )
        return history

    # ==================== Student Context Query Methods ====================

    async def get_struggling_concepts(self, user_id: str) -> list[dict]:
        """Get concepts where student is struggling (not understood or explained 2+ times)."""
        concepts = []

        # From concept_understanding: not understood
        async with self.conn.execute(
            """
            SELECT pattern_id, concept, notes FROM concept_understanding
            WHERE user_id = ? AND understood = 0
            """,
            (user_id,),
        ) as cursor:
            async for row in cursor:
                concepts.append(
                    {
                        "pattern_id": row["pattern_id"],
                        "concept": row["concept"],
                        "source": "not_understood",
                        "notes": row["notes"],
                    }
                )

        # From teaching_history: explained 2+ times
        async with self.conn.execute(
            """
            SELECT pattern_id, concept, explanation_count FROM teaching_history
            WHERE user_id = ? AND explanation_count >= 2
            """,
            (user_id,),
        ) as cursor:
            async for row in cursor:
                # Avoid duplicates
                if not any(
                    c["pattern_id"] == row["pattern_id"]
                    and c["concept"] == row["concept"]
                    for c in concepts
                ):
                    concepts.append(
                        {
                            "pattern_id": row["pattern_id"],
                            "concept": row["concept"],
                            "source": "multiple_explanations",
                            "explanation_count": row["explanation_count"],
                        }
                    )

        return concepts

    async def get_mastered_concepts(self, user_id: str) -> list[dict]:
        """Get concepts that student has mastered."""
        concepts = []
        async with self.conn.execute(
            """
            SELECT pattern_id, concept, taught_at FROM concept_understanding
            WHERE user_id = ? AND understood = 1
            """,
            (user_id,),
        ) as cursor:
            async for row in cursor:
                concepts.append(
                    {
                        "pattern_id": row["pattern_id"],
                        "concept": row["concept"],
                        "taught_at": row["taught_at"],
                    }
                )
        return concepts
