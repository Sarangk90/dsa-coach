"""Tests for database operations."""

import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from dsa_coach.storage.db import Database
from dsa_coach.storage.models import PatternProgress, QuestCompletion


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
async def test_create_session(test_db):
    """Test creating a new session."""
    session = await test_db.create_session(
        user_id="test_user",
        session_type="practice",
        current_pattern="sliding_window",
    )

    assert session.id is not None
    assert session.user_id == "test_user"
    assert session.session_type == "practice"
    assert session.current_pattern == "sliding_window"


@pytest.mark.asyncio
async def test_get_session(test_db):
    """Test retrieving a session."""
    created = await test_db.create_session(user_id="test_user")

    retrieved = await test_db.get_session(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id


@pytest.mark.asyncio
async def test_get_latest_session(test_db):
    """Test getting the most recent session."""
    await test_db.create_session(user_id="test_user", session_type="old")
    await test_db.create_session(user_id="test_user", session_type="new")

    retrieved = await test_db.get_latest_session("test_user")

    assert retrieved is not None
    assert retrieved.session_type == "new"


@pytest.mark.asyncio
async def test_add_message(test_db):
    """Test adding messages to a session."""
    session = await test_db.create_session()

    msg = await test_db.add_message(
        session_id=session.id,
        role="user",
        content="Hello, coach!",
    )

    assert msg.id is not None
    assert msg.role == "user"
    assert msg.content == "Hello, coach!"


@pytest.mark.asyncio
async def test_get_messages(test_db):
    """Test retrieving messages for a session."""
    session = await test_db.create_session()

    await test_db.add_message(session.id, "user", "First")
    await test_db.add_message(session.id, "assistant", "Second")
    await test_db.add_message(session.id, "user", "Third")

    messages = await test_db.get_messages(session.id)

    assert len(messages) == 3
    assert messages[0].content == "First"
    assert messages[1].content == "Second"
    assert messages[2].content == "Third"


@pytest.mark.asyncio
async def test_user_profile_create_on_get(test_db):
    """Test that profile is created if it doesn't exist."""
    profile = await test_db.get_or_create_profile("new_user")

    assert profile.id == "new_user"
    assert profile.total_xp == 0
    assert profile.current_rank == "Novice"


@pytest.mark.asyncio
async def test_update_profile(test_db):
    """Test updating user profile."""
    profile = await test_db.get_or_create_profile("test_user")
    profile.total_xp = 500
    profile.current_rank = "Apprentice"

    await test_db.update_profile(profile)

    retrieved = await test_db.get_or_create_profile("test_user")
    assert retrieved.total_xp == 500
    assert retrieved.current_rank == "Apprentice"


@pytest.mark.asyncio
async def test_pattern_progress(test_db):
    """Test pattern progress operations."""
    progress = PatternProgress(
        id="default_sliding_window",
        user_id="default",
        pattern_id="sliding_window",
        confidence=50,
        quests_completed=2,
    )

    await test_db.upsert_pattern_progress(progress)

    retrieved = await test_db.get_pattern_progress("default", "sliding_window")
    assert retrieved is not None
    assert retrieved.confidence == 50
    assert retrieved.quests_completed == 2


@pytest.mark.asyncio
async def test_quest_completion(test_db):
    """Test quest completion operations."""
    completion = QuestCompletion(
        id="default_two_sum",
        user_id="default",
        quest_id="two_sum",
        pattern_id="hash_map",
        xp_earned=100,
        hints_used=1,
    )

    await test_db.upsert_quest_completion(completion)

    retrieved = await test_db.get_quest_completion("default", "two_sum")
    assert retrieved is not None
    assert retrieved.xp_earned == 100
    assert retrieved.hints_used == 1


@pytest.mark.asyncio
async def test_get_completed_quests(test_db):
    """Test getting all completed quests."""
    for i in range(3):
        completion = QuestCompletion(
            id=f"default_quest_{i}",
            user_id="default",
            quest_id=f"quest_{i}",
            pattern_id="test_pattern",
        )
        await test_db.upsert_quest_completion(completion)

    completions = await test_db.get_completed_quests("default")
    assert len(completions) == 3


@pytest.mark.asyncio
async def test_get_all_pattern_progress(test_db):
    """Test getting progress for all patterns."""
    for pattern in ["sliding_window", "two_pointers", "hash_map"]:
        progress = PatternProgress(
            id=f"default_{pattern}",
            user_id="default",
            pattern_id=pattern,
            confidence=30,
        )
        await test_db.upsert_pattern_progress(progress)

    all_progress = await test_db.get_all_pattern_progress("default")
    assert len(all_progress) == 3
