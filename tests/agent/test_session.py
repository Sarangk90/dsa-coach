"""Tests for SessionManager."""

import pytest
import pytest_asyncio
import tempfile
from pathlib import Path

from dsa_coach.storage.db import Database
from dsa_coach.agent.session import SessionManager


@pytest_asyncio.fixture
async def test_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    db = Database(db_path)
    await db.connect()
    
    yield db
    
    await db.close()
    db_path.unlink(missing_ok=True)


@pytest_asyncio.fixture
async def session_manager(test_db):
    """Create a SessionManager for testing."""
    manager = SessionManager(test_db)
    await manager.start_or_resume()
    return manager


@pytest.mark.asyncio
async def test_start_new_session(test_db):
    """Test starting a new session."""
    manager = SessionManager(test_db)
    session = await manager.start_or_resume()
    
    assert session is not None
    assert session.id is not None
    assert manager.session == session


@pytest.mark.asyncio
async def test_add_user_message(session_manager):
    """Test adding a user message."""
    message = await session_manager.add_user_message("Hello, coach!")
    
    assert message.role == "user"
    assert message.content == "Hello, coach!"
    
    # Message should be in history
    assert len(session_manager.messages) == 1
    assert session_manager.messages[0]["content"] == "Hello, coach!"


@pytest.mark.asyncio
async def test_add_assistant_message(session_manager):
    """Test adding an assistant message."""
    message = await session_manager.add_assistant_message("Hello! How can I help?")
    
    assert message.role == "assistant"
    assert message.content == "Hello! How can I help?"
    
    # Message should be in history
    assert len(session_manager.messages) == 1


@pytest.mark.asyncio
async def test_conversation_flow(session_manager):
    """Test a conversation with multiple messages."""
    await session_manager.add_user_message("Hi!")
    await session_manager.add_assistant_message("Hello!")
    await session_manager.add_user_message("How are you?")
    await session_manager.add_assistant_message("I'm doing well!")
    
    messages = session_manager.get_messages_for_llm()
    
    assert len(messages) == 4
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "user"
    assert messages[3]["role"] == "assistant"


@pytest.mark.asyncio
async def test_update_context(session_manager):
    """Test updating session context."""
    await session_manager.update_context(
        pattern_id="sliding_window",
        quest_id="two_sum",
    )
    
    assert session_manager.session.current_pattern == "sliding_window"
    assert session_manager.session.current_quest == "two_sum"


@pytest.mark.asyncio
async def test_get_context_summary(session_manager):
    """Test getting context summary."""
    await session_manager.update_context(pattern_id="sliding_window")
    await session_manager.add_user_message("Hello")
    
    summary = await session_manager.get_context_summary()
    
    assert summary["active"] is True
    assert summary["current_pattern"] == "sliding_window"
    assert summary["message_count"] == 1


@pytest.mark.asyncio
async def test_add_tool_call(session_manager):
    """Test recording a tool call."""
    message = await session_manager.add_tool_call(
        tool_name="list_patterns",
        tool_args={"limit": 5},
        tool_id="call_123",
    )
    
    assert message.role == "tool_call"
    assert message.tool_name == "list_patterns"


@pytest.mark.asyncio
async def test_add_tool_result(session_manager):
    """Test recording a tool result."""
    message = await session_manager.add_tool_result(
        tool_name="list_patterns",
        tool_id="call_123",
        result='{"patterns": []}',
    )
    
    assert message.role == "tool_result"
    assert message.tool_name == "list_patterns"

