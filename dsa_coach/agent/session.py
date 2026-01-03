"""Session manager for DSA Coach agent.

Handles session persistence, message history, and resumption.
"""

from __future__ import annotations

from datetime import datetime

from ..storage.db import Database
from ..storage.models import Message, Session


class SessionManager:
    """Manages coaching sessions and message history."""

    def __init__(self, db: Database, user_id: str = "default"):
        self.db = db
        self.user_id = user_id
        self._current_session: Session | None = None
        self._messages: list[dict] = []

    @property
    def session(self) -> Session | None:
        """Get current session."""
        return self._current_session

    @property
    def messages(self) -> list[dict]:
        """Get message history for LLM context."""
        return self._messages

    async def start_or_resume(
        self,
        session_type: str = "general",
        pattern_id: str | None = None,
    ) -> Session:
        """
        Start a new session or resume the most recent one.

        Args:
            session_type: Type of session (general, learn, practice)
            pattern_id: Optional pattern to focus on

        Returns:
            The session (new or resumed)
        """
        # Try to resume recent session
        latest = await self.db.get_latest_session(self.user_id)

        if latest:
            # Check if session is recent (within last 30 minutes)
            age = datetime.now() - latest.updated_at
            if age.total_seconds() < 1800:  # 30 minutes
                self._current_session = latest
                await self._load_messages()
                return latest

        # Create new session
        self._current_session = await self.db.create_session(
            user_id=self.user_id,
            session_type=session_type,
            current_pattern=pattern_id,
        )
        self._messages = []
        return self._current_session

    async def _load_messages(self, limit: int = 50) -> None:
        """Load message history from database."""
        if not self._current_session:
            return

        db_messages = await self.db.get_messages(self._current_session.id, limit=limit)

        self._messages = []
        for msg in db_messages:
            if msg.role in ("user", "assistant"):
                self._messages.append(
                    {
                        "role": msg.role,
                        "content": msg.content,
                    }
                )
            elif msg.role == "tool_result":
                # Format tool results for context
                self._messages.append(
                    {
                        "role": "user",
                        "content": f"[Tool Result: {msg.tool_name}]\n{msg.content}",
                    }
                )

    async def add_user_message(self, content: str) -> Message:
        """Add a user message to the session."""
        if not self._current_session:
            raise RuntimeError("No active session. Call start_or_resume first.")

        message = await self.db.add_message(
            session_id=self._current_session.id,
            role="user",
            content=content,
        )

        self._messages.append({"role": "user", "content": content})
        return message

    async def add_assistant_message(self, content: str) -> Message:
        """Add an assistant message to the session."""
        if not self._current_session:
            raise RuntimeError("No active session. Call start_or_resume first.")

        message = await self.db.add_message(
            session_id=self._current_session.id,
            role="assistant",
            content=content,
        )

        self._messages.append({"role": "assistant", "content": content})
        return message

    async def add_tool_call(
        self,
        tool_name: str,
        tool_args: dict,
        tool_id: str,
    ) -> Message:
        """Record a tool call."""
        if not self._current_session:
            raise RuntimeError("No active session.")

        return await self.db.add_message(
            session_id=self._current_session.id,
            role="tool_call",
            content=f"Calling {tool_name}",
            tool_name=tool_name,
            tool_args=tool_args,
        )

    async def add_tool_result(
        self,
        tool_name: str,
        tool_id: str,
        result: str,
        is_error: bool = False,
    ) -> Message:
        """Record a tool result."""
        if not self._current_session:
            raise RuntimeError("No active session.")

        return await self.db.add_message(
            session_id=self._current_session.id,
            role="tool_result",
            content=result,
            tool_name=tool_name,
        )

    async def update_context(
        self,
        pattern_id: str | None = None,
        quest_id: str | None = None,
    ) -> None:
        """Update session context."""
        if not self._current_session:
            return

        if pattern_id is not None:
            self._current_session.current_pattern = pattern_id
        if quest_id is not None:
            self._current_session.current_quest = quest_id

        await self.db.update_session(self._current_session)

    async def get_context_summary(self) -> dict:
        """Get a summary of the current session context."""
        if not self._current_session:
            return {"active": False}

        return {
            "active": True,
            "session_id": self._current_session.id,
            "session_type": self._current_session.session_type,
            "current_pattern": self._current_session.current_pattern,
            "current_quest": self._current_session.current_quest,
            "message_count": len(self._messages),
            "started_at": self._current_session.created_at.isoformat(),
        }

    def get_messages_for_llm(self) -> list[dict]:
        """
        Get messages formatted for LLM context.

        Keeps only user/assistant messages for clean context.
        """
        return [m for m in self._messages if m.get("role") in ("user", "assistant")]
