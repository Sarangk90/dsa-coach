"""SQLite database wrapper for DSA Coach.

Provides async database operations with automatic migrations.
The Database class composes domain-specific mixins for a clean public API.
"""

from pathlib import Path

import aiosqlite

from .db_learning import LearningMixin
from .db_profiles import ProfileMixin
from .db_progress import ProgressMixin
from .db_quests import QuestMixin
from .db_sessions import SessionMixin
from .schema import SCHEMA_SQL

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "coach.db"

# Schema version for migrations
SCHEMA_VERSION = (
    5  # v5: Added UNIQUE constraints for idempotency + derived stats methods
)


class Database(SessionMixin, ProfileMixin, ProgressMixin, QuestMixin, LearningMixin):
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

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb) -> None:
        await self.close()

    @property
    def conn(self) -> aiosqlite.Connection:
        """Get active connection, raising if not connected."""
        if not self._connection:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._connection

    async def _ensure_schema(self) -> None:
        """Create tables if they don't exist."""
        await self.conn.executescript(SCHEMA_SQL)
        await self.conn.commit()

        # Migration: Add thinking column if it doesn't exist (for existing DBs)
        await self._migrate_add_thinking_column()

    async def _migrate_add_thinking_column(self) -> None:
        """Add thinking and thinking_signature columns to messages table if missing."""
        # Check if columns exist
        async with self.conn.execute("PRAGMA table_info(messages)") as cursor:
            columns = [row["name"] async for row in cursor]

        if "thinking" not in columns:
            await self.conn.execute("ALTER TABLE messages ADD COLUMN thinking TEXT")
        if "thinking_signature" not in columns:
            await self.conn.execute(
                "ALTER TABLE messages ADD COLUMN thinking_signature TEXT"
            )
        await self.conn.commit()

        # Run confidence -> progress migration
        await self._migrate_confidence_to_progress()

    async def _migrate_confidence_to_progress(self) -> None:
        """Rename 'confidence' column to 'progress' in pattern_progress table.

        SQLite doesn't support ALTER TABLE RENAME COLUMN in older versions,
        so we check if the old column exists and add the new one if needed.
        """
        async with self.conn.execute("PRAGMA table_info(pattern_progress)") as cursor:
            columns = [row["name"] async for row in cursor]

        # If 'confidence' exists but 'progress' doesn't, we need to migrate
        if "confidence" in columns and "progress" not in columns:
            # Add the new column
            await self.conn.execute(
                "ALTER TABLE pattern_progress ADD COLUMN progress INTEGER NOT NULL DEFAULT 0"
            )
            # Copy data from old column to new
            await self.conn.execute("UPDATE pattern_progress SET progress = confidence")
            await self.conn.commit()

        # Create the progress index (after migration ensures column exists)
        await self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_pattern_progress_progress ON pattern_progress(progress)"
        )
        await self.conn.commit()
