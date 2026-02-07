"""Session manager for DSA Coach agent.

Handles session persistence, message history, and resumption.
"""

from __future__ import annotations

from ..ai.client import THINKING_BUDGET
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
        Start a new session.

        Args:
            session_type: Type of session (general, learn, practice)
            pattern_id: Optional pattern to focus on

        Returns:
            The new session

        Note:
            Use /resume command to manually resume a previous session.
        """
        # Always create a fresh session - use /resume to continue old ones
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
            if msg.role == "user":
                self._messages.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                # Store with thinking and signature if available
                self._messages.append(
                    {
                        "role": "assistant",
                        "content": msg.content,
                        "thinking": msg.thinking,  # May be None for old messages
                        "thinking_signature": msg.thinking_signature,  # Required for replay
                    }
                )
            elif msg.role == "tool_result":
                # Preserve tool results as a distinct role so display filtering
                # can exclude them while LLM formatting can still include them.
                self._messages.append(
                    {
                        "role": "tool_result",
                        "tool_name": msg.tool_name,
                        "content": msg.content,
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

    async def add_assistant_message(
        self,
        content: str,
        thinking: str | None = None,
        thinking_signature: str | None = None,
    ) -> Message:
        """Add an assistant message to the session.

        Args:
            content: The text content of the message
            thinking: Optional extended thinking content from Claude
            thinking_signature: Signature for thinking block (required for replay)
        """
        if not self._current_session:
            raise RuntimeError("No active session. Call start_or_resume first.")

        message = await self.db.add_message(
            session_id=self._current_session.id,
            role="assistant",
            content=content,
            thinking=thinking,
            thinking_signature=thinking_signature,
        )

        self._messages.append(
            {
                "role": "assistant",
                "content": content,
                "thinking": thinking,
                "thinking_signature": thinking_signature,
            }
        )
        return message

    async def add_tool_call(
        self,
        tool_name: str,
        tool_args: dict,
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

        When extended thinking is enabled:
        - User messages are always included as plain strings
        - Assistant messages WITH thinking+signature use block format
        - Assistant messages WITHOUT thinking+signature use plain string format

        This keeps all context while allowing thinking to stay enabled.
        Plain string assistant messages are valid even when thinking is enabled.
        """
        result = []
        for m in self._messages:
            role = m.get("role")
            if role == "user":
                result.append({"role": "user", "content": m.get("content", "")})
            elif role == "assistant":
                content = m.get("content", "")
                thinking = m.get("thinking")
                thinking_signature = m.get("thinking_signature")

                if THINKING_BUDGET > 0 and thinking and thinking_signature:
                    # Has stored thinking WITH signature - use block format
                    blocks = [
                        {
                            "type": "thinking",
                            "thinking": thinking,
                            "signature": thinking_signature,
                        },
                        {"type": "text", "text": content},
                    ]
                    result.append({"role": "assistant", "content": blocks})
                else:
                    # Plain string content remains valid when thinking is enabled.
                    result.append({"role": "assistant", "content": content})
            elif role == "tool_result":
                tool_name = m.get("tool_name") or "tool"
                tool_content = m.get("content", "")
                result.append(
                    {
                        "role": "user",
                        "content": f"[Tool Result: {tool_name}]\n{tool_content}",
                    }
                )

        return result

    def has_messages_without_thinking(self) -> bool:
        """Check if any assistant messages lack stored thinking content and signature.

        Used to determine if extended thinking should be disabled for this call.
        Returns True if there are assistant messages without complete thinking data.
        """
        for m in self._messages:
            if m.get("role") == "assistant":
                # Need BOTH thinking AND signature for proper replay
                if not m.get("thinking") or not m.get("thinking_signature"):
                    return True
        return False

    async def resume_by_id(self, session_id: str) -> Session | None:
        """Resume a specific session by ID (for /resume command).

        - Fetches session from DB
        - Loads full message history
        - Sets as current session
        - Returns Session if found, None otherwise
        """
        session = await self.db.get_session(session_id)
        if not session:
            return None

        self._current_session = session
        await self._load_messages()  # Reuse existing method
        return session

    def get_display_messages(self) -> list[dict]:
        """Get all user/assistant messages for display after resume.

        Returns list of {"role": str, "content": str} dicts.
        Filters to only user and assistant messages (no tool calls).
        """
        return [
            {"role": m["role"], "content": m["content"]}
            for m in self._messages
            if m.get("role") in ("user", "assistant")
        ]
