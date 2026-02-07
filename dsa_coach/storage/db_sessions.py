"""Session and Message database operations mixin."""

from __future__ import annotations

import json
import uuid
from datetime import datetime

import aiosqlite

from .models import Message, Session


class SessionMixin:
    """Mixin providing session and message CRUD operations."""

    conn: aiosqlite.Connection

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

    async def list_sessions(
        self,
        user_id: str = "default",
        limit: int = 10,
        exclude_session_id: str | None = None,
    ) -> list[dict]:
        """List recent sessions with preview info for /resume picker.

        Returns list of dicts with:
        - id, created_at, updated_at, session_type
        - current_pattern, current_quest
        - message_count
        - first_message (first user message content)

        Filters out:
        - Sessions with 0 messages
        - The current session (if exclude_session_id provided)

        Orders by updated_at DESC.
        """
        query = """
            SELECT
                s.id,
                s.created_at,
                s.updated_at,
                s.session_type,
                s.current_pattern,
                s.current_quest,
                COUNT(m.id) as message_count,
                (SELECT content FROM messages m2
                 WHERE m2.session_id = s.id AND m2.role = 'user'
                 ORDER BY m2.created_at LIMIT 1) as first_message
            FROM sessions s
            LEFT JOIN messages m ON s.id = m.session_id
            WHERE s.user_id = ?
              AND (? IS NULL OR s.id != ?)
            GROUP BY s.id
            HAVING COUNT(m.id) > 0
            ORDER BY s.updated_at DESC
            LIMIT ?
        """
        sessions = []
        async with self.conn.execute(
            query, (user_id, exclude_session_id, exclude_session_id, limit)
        ) as cursor:
            async for row in cursor:
                sessions.append(
                    {
                        "id": row["id"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "session_type": row["session_type"],
                        "current_pattern": row["current_pattern"],
                        "current_quest": row["current_quest"],
                        "message_count": row["message_count"],
                        "first_message": row["first_message"],
                    }
                )
        return sessions

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
        thinking: str | None = None,
        thinking_signature: str | None = None,
        tool_name: str | None = None,
        tool_args: dict | None = None,
    ) -> Message:
        """Add a message to a session."""
        message = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            thinking=thinking,
            thinking_signature=thinking_signature,
            tool_name=tool_name,
            tool_args=tool_args,
            created_at=datetime.now(),
        )
        await self.conn.execute(
            """
            INSERT INTO messages (id, session_id, role, content, thinking, thinking_signature, tool_name, tool_args, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message.id,
                message.session_id,
                message.role,
                message.content,
                message.thinking,
                message.thinking_signature,
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
                # Handle thinking columns (may not exist in older DBs)
                thinking = None
                thinking_signature = None
                try:
                    thinking = row["thinking"]
                    thinking_signature = row["thinking_signature"]
                except (IndexError, KeyError):
                    pass

                messages.append(
                    Message(
                        id=row["id"],
                        session_id=row["session_id"],
                        role=row["role"],
                        content=row["content"],
                        thinking=thinking,
                        thinking_signature=thinking_signature,
                        tool_name=row["tool_name"],
                        tool_args=json.loads(row["tool_args"])
                        if row["tool_args"]
                        else None,
                        created_at=datetime.fromisoformat(row["created_at"]),
                    )
                )
        return messages
