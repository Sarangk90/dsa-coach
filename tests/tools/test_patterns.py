"""Tests for pattern tools."""

import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from dsa_coach.storage.db import Database
from dsa_coach.tools.patterns import (
    get_next_essential_quest,
    get_pattern_details,
    get_weak_patterns,
    list_patterns,
)


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
async def test_list_patterns(test_db):
    """Test listing all patterns."""
    result = await list_patterns(test_db)

    assert result.success
    assert result.data is not None
    assert len(result.data) > 0

    # Check that sliding_window is present
    pattern_ids = [p["pattern_id"] for p in result.data]
    assert "sliding_window" in pattern_ids


@pytest.mark.asyncio
async def test_list_patterns_includes_confidence(test_db):
    """Test that patterns include confidence scores."""
    result = await list_patterns(test_db)

    assert result.success
    for pattern in result.data:
        assert "confidence" in pattern
        assert "quests_completed" in pattern


@pytest.mark.asyncio
async def test_get_pattern_details(test_db):
    """Test getting details for a specific pattern."""
    result = await get_pattern_details(test_db, "sliding_window")

    assert result.success
    assert result.data is not None
    assert result.data["pattern_id"] == "sliding_window"
    assert "concepts" in result.data
    assert "essential_quests" in result.data


@pytest.mark.asyncio
async def test_get_pattern_details_not_found(test_db):
    """Test getting details for non-existent pattern."""
    result = await get_pattern_details(test_db, "nonexistent_pattern")

    assert not result.success
    assert result.error is not None


@pytest.mark.asyncio
async def test_get_weak_patterns(test_db):
    """Test getting patterns with lowest confidence."""
    result = await get_weak_patterns(test_db, limit=3)

    assert result.success
    assert result.data is not None
    assert len(result.data) <= 3

    # All patterns should have low confidence (0) initially
    for pattern in result.data:
        assert pattern["confidence"] == 0


@pytest.mark.asyncio
async def test_get_next_essential_quest(test_db):
    """Test getting next essential quest for a pattern."""
    result = await get_next_essential_quest(test_db, "sliding_window")

    assert result.success
    # sliding_window has essential_questions defined
    if result.data:
        assert "quest_id" in result.data
        assert "title" in result.data


@pytest.mark.asyncio
async def test_get_next_essential_quest_not_found(test_db):
    """Test getting next essential quest for non-existent pattern."""
    result = await get_next_essential_quest(test_db, "nonexistent")

    assert not result.success
