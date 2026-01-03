"""SQLite database wrapper for DSA Coach.

Provides async database operations with automatic migrations.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

import aiosqlite

from .models import (
    ConceptUnderstanding,
    Message,
    PatternProgress,
    QuestCompletion,
    Session,
    UserProfile,
)

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "coach.db"

# Schema version for migrations
SCHEMA_VERSION = 4  # v4: Added deep student model (mistakes, daily_logs, milestones, teaching_history)


class Database:
    """Async SQLite database wrapper with connection pooling."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Open database connection and ensure schema exists."""
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        await self._ensure_schema()

    async def close(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def __aenter__(self) -> "Database":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    @property
    def conn(self) -> aiosqlite.Connection:
        """Get active connection, raising if not connected."""
        if not self._connection:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._connection

    async def _ensure_schema(self) -> None:
        """Create tables if they don't exist."""
        await self.conn.executescript("""
            -- Sessions table
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'default',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                current_pattern TEXT,
                current_quest TEXT,
                session_type TEXT NOT NULL DEFAULT 'general',
                metadata TEXT NOT NULL DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at DESC);

            -- Messages table
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_name TEXT,
                tool_args TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
            CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);

            -- User profiles table
            CREATE TABLE IF NOT EXISTS user_profiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL DEFAULT 'DSA Learner',
                quests_completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                last_active TEXT NOT NULL
            );

            -- Pattern progress table
            CREATE TABLE IF NOT EXISTS pattern_progress (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'default',
                pattern_id TEXT NOT NULL,
                confidence INTEGER NOT NULL DEFAULT 0,
                quests_completed INTEGER NOT NULL DEFAULT 0,
                quests_total INTEGER NOT NULL DEFAULT 0,
                concepts_understood TEXT NOT NULL DEFAULT '[]',
                concepts_total INTEGER NOT NULL DEFAULT 0,
                last_practiced TEXT,
                next_review TEXT,
                mastered INTEGER NOT NULL DEFAULT 0,
                UNIQUE(user_id, pattern_id)
            );
            CREATE INDEX IF NOT EXISTS idx_pattern_progress_user ON pattern_progress(user_id);
            CREATE INDEX IF NOT EXISTS idx_pattern_progress_confidence ON pattern_progress(confidence);

            -- Quest completions table
            CREATE TABLE IF NOT EXISTS quest_completions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'default',
                quest_id TEXT NOT NULL,
                pattern_id TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                time_minutes INTEGER,
                hints_used INTEGER NOT NULL DEFAULT 0,
                success INTEGER NOT NULL DEFAULT 1,
                review_count INTEGER NOT NULL DEFAULT 0,
                last_reviewed TEXT,
                next_review_in INTEGER NOT NULL DEFAULT 1,
                UNIQUE(user_id, quest_id)
            );
            CREATE INDEX IF NOT EXISTS idx_quest_completions_user ON quest_completions(user_id);
            CREATE INDEX IF NOT EXISTS idx_quest_completions_pattern ON quest_completions(pattern_id);

            -- Concept understanding table
            CREATE TABLE IF NOT EXISTS concept_understanding (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'default',
                pattern_id TEXT NOT NULL,
                concept TEXT NOT NULL,
                understood INTEGER NOT NULL DEFAULT 0,
                diagnosed_at TEXT,
                taught_at TEXT,
                notes TEXT NOT NULL DEFAULT '',
                UNIQUE(user_id, pattern_id, concept)
            );
            CREATE INDEX IF NOT EXISTS idx_concept_understanding_pattern ON concept_understanding(pattern_id);

            -- ============ Deep Student Model Tables (v4) ============

            -- Mistakes with pattern recognition
            CREATE TABLE IF NOT EXISTS mistakes (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'default',
                quest_id TEXT NOT NULL,
                pattern_id TEXT NOT NULL,
                mistake_type TEXT NOT NULL,
                description TEXT NOT NULL,
                lesson_learned TEXT,
                logged_at TEXT NOT NULL,
                recurrence_count INTEGER DEFAULT 1
            );
            CREATE INDEX IF NOT EXISTS idx_mistakes_user ON mistakes(user_id);
            CREATE INDEX IF NOT EXISTS idx_mistakes_type ON mistakes(user_id, mistake_type);
            CREATE INDEX IF NOT EXISTS idx_mistakes_pattern ON mistakes(user_id, pattern_id);

            -- Daily activity logs
            CREATE TABLE IF NOT EXISTS daily_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'default',
                date TEXT NOT NULL,
                problems_solved INTEGER NOT NULL DEFAULT 0,
                time_spent_mins INTEGER NOT NULL DEFAULT 0,
                patterns_worked TEXT NOT NULL DEFAULT '[]',
                hints_used INTEGER NOT NULL DEFAULT 0,
                UNIQUE(user_id, date)
            );
            CREATE INDEX IF NOT EXISTS idx_daily_logs_user_date ON daily_logs(user_id, date);

            -- Milestones and wins
            CREATE TABLE IF NOT EXISTS milestones (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'default',
                milestone_type TEXT NOT NULL,
                pattern_id TEXT,
                quest_id TEXT,
                description TEXT NOT NULL,
                achieved_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_milestones_user ON milestones(user_id);
            CREATE INDEX IF NOT EXISTS idx_milestones_achieved ON milestones(achieved_at DESC);

            -- Teaching history
            CREATE TABLE IF NOT EXISTS teaching_history (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'default',
                pattern_id TEXT NOT NULL,
                concept TEXT NOT NULL,
                explanation_count INTEGER DEFAULT 1,
                last_explained TEXT NOT NULL,
                student_response TEXT,
                UNIQUE(user_id, pattern_id, concept)
            );
            CREATE INDEX IF NOT EXISTS idx_teaching_history_pattern ON teaching_history(user_id, pattern_id);

            -- Schema version table
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            );
        """)
        await self.conn.commit()

    # ==================== Session Operations ====================

    async def create_session(
        self,
        user_id: str = "default",
        session_type: str = "general",
        current_pattern: str | None = None,
        current_quest: str | None = None,
    ) -> Session:
        """Create a new coaching session."""
        now = datetime.now()
        session = Session(
            id=str(uuid.uuid4()),
            user_id=user_id,
            created_at=now,
            updated_at=now,
            current_pattern=current_pattern,
            current_quest=current_quest,
            session_type=session_type,
        )
        await self.conn.execute(
            """
            INSERT INTO sessions (id, user_id, created_at, updated_at, current_pattern, current_quest, session_type, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session.id,
                session.user_id,
                session.created_at.isoformat(),
                session.updated_at.isoformat(),
                session.current_pattern,
                session.current_quest,
                session.session_type,
                json.dumps(session.metadata),
            ),
        )
        await self.conn.commit()
        return session

    async def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID."""
        async with self.conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_session(row)
            return None

    async def get_latest_session(self, user_id: str = "default") -> Session | None:
        """Get the most recent session for a user."""
        async with self.conn.execute(
            "SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_session(row)
            return None

    async def update_session(self, session: Session) -> None:
        """Update a session."""
        session.updated_at = datetime.now()
        await self.conn.execute(
            """
            UPDATE sessions SET
                updated_at = ?, current_pattern = ?, current_quest = ?,
                session_type = ?, metadata = ?
            WHERE id = ?
            """,
            (
                session.updated_at.isoformat(),
                session.current_pattern,
                session.current_quest,
                session.session_type,
                json.dumps(session.metadata),
                session.id,
            ),
        )
        await self.conn.commit()

    def _row_to_session(self, row: aiosqlite.Row) -> Session:
        """Convert a database row to a Session model."""
        return Session(
            id=row["id"],
            user_id=row["user_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            current_pattern=row["current_pattern"],
            current_quest=row["current_quest"],
            session_type=row["session_type"],
            metadata=json.loads(row["metadata"]),
        )

    # ==================== Message Operations ====================

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_name: str | None = None,
        tool_args: dict | None = None,
    ) -> Message:
        """Add a message to a session."""
        message = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            tool_name=tool_name,
            tool_args=tool_args,
            created_at=datetime.now(),
        )
        await self.conn.execute(
            """
            INSERT INTO messages (id, session_id, role, content, tool_name, tool_args, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message.id,
                message.session_id,
                message.role,
                message.content,
                message.tool_name,
                json.dumps(message.tool_args) if message.tool_args else None,
                message.created_at.isoformat(),
            ),
        )
        await self.conn.commit()
        return message

    async def get_messages(
        self, session_id: str, limit: int | None = None
    ) -> list[Message]:
        """Get messages for a session, ordered by creation time."""
        query = "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at"
        if limit:
            query += f" DESC LIMIT {limit}"
            query = f"SELECT * FROM ({query}) ORDER BY created_at"

        messages = []
        async with self.conn.execute(query, (session_id,)) as cursor:
            async for row in cursor:
                messages.append(
                    Message(
                        id=row["id"],
                        session_id=row["session_id"],
                        role=row["role"],
                        content=row["content"],
                        tool_name=row["tool_name"],
                        tool_args=json.loads(row["tool_args"])
                        if row["tool_args"]
                        else None,
                        created_at=datetime.fromisoformat(row["created_at"]),
                    )
                )
        return messages

    # ==================== User Profile Operations ====================

    async def get_or_create_profile(self, user_id: str = "default") -> UserProfile:
        """Get user profile, creating if it doesn't exist."""
        async with self.conn.execute(
            "SELECT * FROM user_profiles WHERE id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return UserProfile(
                    id=row["id"],
                    name=row["name"],
                    quests_completed=row["quests_completed"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    last_active=datetime.fromisoformat(row["last_active"]),
                )

        # Create new profile
        now = datetime.now()
        profile = UserProfile(id=user_id, created_at=now, last_active=now)
        await self.conn.execute(
            """
            INSERT INTO user_profiles (id, name, quests_completed, created_at, last_active)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                profile.id,
                profile.name,
                profile.quests_completed,
                profile.created_at.isoformat(),
                profile.last_active.isoformat(),
            ),
        )
        await self.conn.commit()
        return profile

    async def update_profile(self, profile: UserProfile) -> None:
        """Update user profile."""
        profile.last_active = datetime.now()
        await self.conn.execute(
            """
            UPDATE user_profiles SET
                name = ?, quests_completed = ?, last_active = ?
            WHERE id = ?
            """,
            (
                profile.name,
                profile.quests_completed,
                profile.last_active.isoformat(),
                profile.id,
            ),
        )
        await self.conn.commit()

    # ==================== Pattern Progress Operations ====================

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
            "SELECT * FROM pattern_progress WHERE user_id = ? ORDER BY confidence",
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
            INSERT INTO pattern_progress (id, user_id, pattern_id, confidence, quests_completed, quests_total, concepts_understood, concepts_total, last_practiced, next_review, mastered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, pattern_id) DO UPDATE SET
                confidence = excluded.confidence,
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
                progress.confidence,
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
        return PatternProgress(
            id=row["id"],
            user_id=row["user_id"],
            pattern_id=row["pattern_id"],
            confidence=row["confidence"],
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

    # ==================== Quest Completion Operations ====================

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
        # Get date 7 days ago
        from datetime import timedelta
        from typing import Any

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
        from datetime import timedelta

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

    async def build_progress_compat(self, user_id: str = "default") -> dict:
        """Build a compatibility dict for code that expects the legacy progress dict format.

        This centralizes the progress_compat construction so all code uses
        consistent data. The returned dict matches the structure expected by
        curriculum.py and other legacy code.

        Returns:
            dict with keys: profile, pattern_proficiency, completed_quests,
            problems_solved, patterns_completed, patterns_in_progress
        """
        patterns = await self.get_all_pattern_progress(user_id)
        completed = await self.get_completed_quests(user_id)
        profile = await self.get_or_create_profile(user_id)
        session = await self.get_latest_session(user_id)

        # Build pattern proficiency dict
        pattern_prof = {}
        for p in patterns:
            pattern_prof[p.pattern_id] = {
                "confidence": p.confidence,
                "attempts": p.quests_completed,
                "successes": p.quests_completed,
                "avg_time_mins": None,
            }

        # Derive patterns_completed from mastered flag
        patterns_completed = [p.pattern_id for p in patterns if p.mastered]

        # Derive patterns_in_progress (has quests but not mastered)
        patterns_in_progress = [
            p.pattern_id for p in patterns if p.quests_completed > 0 and not p.mastered
        ]

        return {
            "profile": {
                "name": profile.name,
                "current_quest": session.current_quest if session else None,
                "active_mode": getattr(profile, "active_mode", None) or "fast_track",
            },
            "pattern_proficiency": pattern_prof,
            "completed_quests": {c.quest_id: True for c in completed},
            "problems_solved": {c.quest_id: True for c in completed},
            "patterns_completed": patterns_completed,
            "patterns_in_progress": patterns_in_progress,
        }
