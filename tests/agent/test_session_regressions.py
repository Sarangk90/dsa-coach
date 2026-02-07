"""Regression tests for session history and resume behavior."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from dsa_coach.agent.session import SessionManager
from dsa_coach.storage.db import Database


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


@pytest.mark.asyncio
async def test_get_messages_for_llm_keeps_thinking_block_when_signature_present(
    test_db,
):
    manager = SessionManager(test_db)
    await manager.start_or_resume()

    await manager.add_user_message("Teach me two pointers")
    await manager.add_assistant_message(
        "Use left/right pointers.",
        thinking="internal reasoning",
        thinking_signature="sig123",
    )

    messages = manager.get_messages_for_llm()
    assert len(messages) == 2
    assert messages[0] == {"role": "user", "content": "Teach me two pointers"}
    assert messages[1]["role"] == "assistant"
    assert isinstance(messages[1]["content"], list)
    assert messages[1]["content"][0]["type"] == "thinking"
    assert messages[1]["content"][0]["signature"] == "sig123"
    assert messages[1]["content"][1]["type"] == "text"


@pytest.mark.asyncio
async def test_get_messages_for_llm_falls_back_to_plain_assistant_text(test_db):
    manager = SessionManager(test_db)
    await manager.start_or_resume()
    await manager.add_assistant_message(
        "Plain response",
        thinking="missing signature branch",
        thinking_signature=None,
    )

    messages = manager.get_messages_for_llm()
    assert messages == [{"role": "assistant", "content": "Plain response"}]


@pytest.mark.asyncio
async def test_has_messages_without_thinking_detects_incomplete_assistant_entries(
    test_db,
):
    manager = SessionManager(test_db)
    await manager.start_or_resume()

    await manager.add_assistant_message("No thinking")
    assert manager.has_messages_without_thinking() is True

    manager2 = SessionManager(test_db)
    await manager2.start_or_resume()
    await manager2.add_assistant_message("With thinking", "reason", "sig")
    assert manager2.has_messages_without_thinking() is False


@pytest.mark.asyncio
async def test_resume_by_id_loads_history_and_formats_tool_results_for_context(test_db):
    first = SessionManager(test_db, user_id="u1")
    session = await first.start_or_resume()
    await first.add_user_message("hello")
    await first.add_assistant_message("hi there")
    await first.add_tool_result("get_dashboard", '{"ok": true}')

    second = SessionManager(test_db, user_id="u1")
    resumed = await second.resume_by_id(session.id)
    assert resumed is not None

    messages_for_llm = second.get_messages_for_llm()
    assert messages_for_llm[0] == {"role": "user", "content": "hello"}
    assert messages_for_llm[1]["role"] == "assistant"
    assert messages_for_llm[2]["role"] == "user"
    assert "[Tool Result: get_dashboard]" in messages_for_llm[2]["content"]

    display_messages = second.get_display_messages()
    assert display_messages == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
    ]


@pytest.mark.asyncio
async def test_resume_by_id_returns_none_for_unknown_session(test_db):
    manager = SessionManager(test_db)
    resumed = await manager.resume_by_id("missing-session-id")
    assert resumed is None
